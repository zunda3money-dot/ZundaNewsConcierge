"""RSS フィード取得 + 過去 N 時間フィルタ + 重複除去。

Usage (standalone):
    python -m scripts.fetch

`scripts.run` からは `fetch_articles(sources, lookback_hours)` を呼び出す。
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

try:
    # python-Levenshtein は C 拡張なので、最悪無くても動くようにフォールバック
    from Levenshtein import ratio as _lev_ratio  # type: ignore
except ImportError:  # pragma: no cover
    from difflib import SequenceMatcher

    def _lev_ratio(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()


logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SOURCES_PATH = ROOT_DIR / "sources.yaml"

USER_AGENT = (
    "Mozilla/5.0 (compatible; ZundamonNewsConcierge/0.1; "
    "+https://github.com/)"
)
HTTP_TIMEOUT_SECONDS = 15
BODY_MAX_CHARS = 3000  # AI に渡す本文の最大文字数
TITLE_SIMILARITY_THRESHOLD = 0.85  # Levenshtein ratio 以上で同一記事とみなす


@dataclass
class Article:
    """1 本のニュース記事を表す。"""

    source: str
    category: str
    title: str
    url: str
    published: dt.datetime  # tz-aware, UTC
    summary: str = ""
    body: str = ""

    # 処理用メタ
    url_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.url_hash = hashlib.sha256(self.url.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["published"] = self.published.isoformat()
        return d


# --------------------------------------------------------------------------- #
# Source loading
# --------------------------------------------------------------------------- #

def load_sources(path: Path | str = DEFAULT_SOURCES_PATH) -> list[dict]:
    """sources.yaml を読み込み、`sources` 配列を返す。"""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    sources = data.get("sources") or []
    if not isinstance(sources, list):
        raise ValueError(f"sources.yaml の 'sources' はリストである必要があります: {path}")
    return sources


# --------------------------------------------------------------------------- #
# Feed fetching
# --------------------------------------------------------------------------- #

def _parse_published(entry) -> dt.datetime | None:
    """feedparser entry から tz-aware UTC datetime を取り出す。"""
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        val = entry.get(key)
        if val:
            try:
                return dt.datetime.fromtimestamp(time.mktime(val), tz=dt.timezone.utc)
            except (OverflowError, ValueError):
                continue
    return None


def _clean_html(text: str) -> str:
    """HTML タグを剥がして空白を詰める。"""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def _fetch_body(url: str) -> str:
    """記事 URL から本文を取得。失敗時は空文字を返す (全体を止めない)。"""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("記事本文取得失敗 url=%s err=%s", url, e)
        return ""

    # chardet でエンコーディング判定
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        try:
            import chardet  # type: ignore

            detected = chardet.detect(resp.content)
            if detected.get("encoding"):
                resp.encoding = detected["encoding"]
        except Exception:  # pragma: no cover
            pass

    soup = BeautifulSoup(resp.text, "html.parser")

    # ノイズ除去
    for tag in soup(["script", "style", "nav", "footer", "aside", "form", "header"]):
        tag.decompose()

    # <article> があれば優先
    article_tag = soup.find("article")
    body_text = (article_tag.get_text(" ", strip=True)
                 if article_tag else soup.get_text(" ", strip=True))
    body_text = re.sub(r"\s+", " ", body_text).strip()
    return body_text[:BODY_MAX_CHARS]


def _fetch_feed(source: dict, lookback: dt.datetime, fetch_body: bool) -> list[Article]:
    name = source.get("name", "unknown")
    url = source.get("url")
    category = source.get("category", "その他")
    if not url:
        logger.warning("source に url が無いためスキップ: %s", name)
        return []

    logger.info("fetch: %s (%s)", name, url)

    try:
        # requests でバイトを取ってから feedparser に渡す (UA を付けるため)
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except requests.RequestException as e:
        logger.warning("フィード取得失敗 source=%s err=%s", name, e)
        return []

    if parsed.bozo and not parsed.entries:
        logger.warning("フィード解析失敗 source=%s err=%s", name, parsed.bozo_exception)
        return []

    articles: list[Article] = []
    for entry in parsed.entries:
        title = _clean_html(entry.get("title", "")).strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        published = _parse_published(entry)
        if published is None:
            # 日付不明は捨てる (過去24hの判定ができないため)
            continue
        if published < lookback:
            continue

        summary = _clean_html(entry.get("summary", ""))[:500]
        body = _fetch_body(link) if fetch_body else ""

        articles.append(
            Article(
                source=name,
                category=category,
                title=title,
                url=link,
                published=published,
                summary=summary,
                body=body,
            )
        )
    logger.info("  → %d 件取得 (過去 %s 以降)", len(articles), lookback.isoformat())
    return articles


# --------------------------------------------------------------------------- #
# Deduplication
# --------------------------------------------------------------------------- #

def _normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[【】\[\]\(\)「」『』・、。,.!?\-—:;'\"]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def dedupe_articles(
    articles: Iterable[Article],
    title_threshold: float = TITLE_SIMILARITY_THRESHOLD,
) -> list[Article]:
    """URL ハッシュ + タイトル Levenshtein 距離で重複除去。"""
    seen_urls: set[str] = set()
    unique: list[Article] = []
    norm_titles: list[str] = []

    for art in sorted(articles, key=lambda a: a.published, reverse=True):
        if art.url_hash in seen_urls:
            continue
        nt = _normalize_title(art.title)
        is_dup = False
        for existing in norm_titles:
            if _lev_ratio(nt, existing) >= title_threshold:
                is_dup = True
                break
        if is_dup:
            continue
        seen_urls.add(art.url_hash)
        norm_titles.append(nt)
        unique.append(art)

    return unique


# --------------------------------------------------------------------------- #
# Public entry
# --------------------------------------------------------------------------- #

def fetch_articles(
    sources: list[dict] | None = None,
    lookback_hours: int = 24,
    fetch_body: bool = True,
) -> list[Article]:
    """全ソースから記事を取得し、重複除去して返す。"""
    if sources is None:
        sources = load_sources()

    now = dt.datetime.now(tz=dt.timezone.utc)
    lookback = now - dt.timedelta(hours=lookback_hours)

    all_articles: list[Article] = []
    for src in sources:
        all_articles.extend(_fetch_feed(src, lookback, fetch_body))

    unique = dedupe_articles(all_articles)
    logger.info("取得合計 %d 件、重複除去後 %d 件", len(all_articles), len(unique))
    return unique


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _cli() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    arts = fetch_articles(fetch_body=False)
    for a in arts[:20]:
        print(f"[{a.published.isoformat()}] {a.source} | {a.title}")
        print(f"  {a.url}")
    print(f"\n合計 {len(arts)} 件")


if __name__ == "__main__":
    _cli()

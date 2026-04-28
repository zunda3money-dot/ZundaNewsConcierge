"""AI による関連度スコアリング + モード別ダイジェスト生成。

対応 AI プロバイダ:
    - "gemini"  → Google Gemini Flash (無料枠)
    - "claude"  → Anthropic Claude Haiku

公開 API:
    - score_articles(articles, config) -> list[ScoredArticle]
    - build_digest(scored, config) -> str
    - summarize(articles, config) -> str  (score + build_digest を通す)
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .fetch import Article

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT_DIR / "prompts"

Mode = Literal["beginner", "expert", "hybrid"]
Provider = Literal["gemini", "claude"]

# スコアリング時に AI に渡す記事本文の長さ
SCORING_BODY_CHARS = 600
# ダイジェスト生成時に AI に渡す記事本文の長さ
DIGEST_BODY_CHARS = 1500
# 1 バッチあたりのスコアリング対象記事数 (長文過ぎる prompt を避ける)
SCORING_BATCH_SIZE = 20

# config.yaml で holdings / interests 両方が空の人向けのデフォルトプロファイル。
# QUICK_START セットアップで「とりあえず動かしてみる」人がメインターゲット。
# 一般的な日本のインデックス投資家がカバーしたいだろう範囲。
DEFAULT_GENERIC_INTERESTS = [
    "S&P500",
    "NASDAQ",
    "新NISA",
    "つみたてNISA",
    "米国株",
    "日本株",
    "日経平均",
    "円安",
    "金利",
    "FRB",
    "日銀",
    "半導体",
    "AI",
    "決算",
]


def _apply_default_profile(config: dict) -> dict:
    """holdings も interests も空のとき、一般市場ニュース向けのデフォルトを当てる。

    元の config は変更せず、コピーを返す。
    """
    holdings = config.get("holdings") or []
    interests = config.get("interests") or []
    if holdings or interests:
        return config
    cfg = dict(config)
    cfg["interests"] = list(DEFAULT_GENERIC_INTERESTS)
    logger.info(
        "config に holdings/interests が無いため、一般市場向けデフォルト interests "
        "(%d 個) を適用しました。",
        len(DEFAULT_GENERIC_INTERESTS),
    )
    return cfg


# --------------------------------------------------------------------------- #
# Data types
# --------------------------------------------------------------------------- #

@dataclass
class ScoredArticle:
    article: Article
    score: int
    reason: str

    def to_dict(self) -> dict:
        return {
            "title": self.article.title,
            "url": self.article.url,
            "source": self.article.source,
            "category": self.article.category,
            "published": self.article.published.isoformat(),
            "summary": self.article.summary,
            "body": self.article.body,
            "score": self.score,
            "reason": self.reason,
        }


# --------------------------------------------------------------------------- #
# Prompt loading / templating
# --------------------------------------------------------------------------- #

def _load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


def _render(template: str, vars: dict[str, str]) -> str:
    out = template
    for k, v in vars.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def _format_list(items: list) -> str:
    if not items:
        return "(なし)"
    return ", ".join(str(x) for x in items)


def _holdings_to_str(holdings: list[dict]) -> str:
    if not holdings:
        return "(なし)"
    return ", ".join(
        f"{h.get('ticker', '?')} ({h.get('name', '')})".strip()
        for h in holdings
    )


# --------------------------------------------------------------------------- #
# AI provider abstraction
# --------------------------------------------------------------------------- #

class AIClient:
    """Gemini / Claude を統一的に扱う薄いラッパ。"""

    def __init__(self, provider: Provider):
        self.provider = provider
        if provider == "gemini":
            self._init_gemini()
        elif provider == "claude":
            self._init_claude()
        else:
            raise ValueError(f"未対応の ai_provider: {provider}")

    def _init_gemini(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY が設定されていません。"
                "GitHub Secrets または .env を確認してください。"
            )
        # 旧 `google-generativeai` パッケージは deprecated。
        # 後継 `google-genai` (google.genai) を使用。
        from google import genai  # type: ignore

        # 無料枠で十分な品質の gemini-2.5-flash をデフォルトに。
        # GEMINI_MODEL 環境変数で上書き可能。
        self._gemini_model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self._gemini_client = genai.Client(api_key=api_key)

    def _init_claude(self) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY が設定されていません。"
                "GitHub Secrets または .env を確認してください。"
            )
        from anthropic import Anthropic  # type: ignore

        self._model_name = os.environ.get(
            "ANTHROPIC_MODEL", "claude-haiku-4-5"
        )
        self._client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        return self._generate_with_retry(prompt, max_tokens=max_tokens)

    def _generate_with_retry(
        self,
        prompt: str,
        max_tokens: int = 2048,
        max_attempts: int = 3,
        base_wait_sec: float = 60.0,
    ) -> str:
        """Gemini/Claude 呼び出し本体 + 一時的エラーへの再試行。

        対象エラー:
          - 503 UNAVAILABLE (Gemini が高負荷で一時的に応答できない)
          - 502 / 504 (上流ゲートウェイ系の一時障害)
          - 429 RATE_LIMITED (短期スパイク; レート制限の一部)

        固定の指数バックオフ (60s → 180s → 300s) で最大 3 回試行。
        SDK 内部のリトライとは別に、外側でロバストに包むイメージ。
        """
        last_err: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                return self._generate_once(prompt, max_tokens=max_tokens)
            except Exception as e:
                if not self._is_transient(e):
                    # 非一時的エラー (例: 認証失敗、無効なモデル名) は即座に上げる
                    raise
                last_err = e
                if attempt == max_attempts:
                    break
                wait = base_wait_sec * attempt  # 60s, 120s, ...
                # 指数寄りに調整: 60, 180, 300
                wait = min(60 * (3 ** (attempt - 1)), 300)
                logger.warning(
                    "AI 呼び出し失敗 (%s) attempt=%d/%d, %.0fs 後にリトライ",
                    type(e).__name__,
                    attempt,
                    max_attempts,
                    wait,
                )
                import time

                time.sleep(wait)
        # 全試行失敗
        raise RuntimeError(
            f"AI 呼び出しが {max_attempts} 回連続で失敗しました: {last_err}"
        ) from last_err

    @staticmethod
    def _is_transient(err: Exception) -> bool:
        """503/502/504/429 等の一時的エラーかどうか。"""
        # google-genai
        try:
            from google.genai import errors as genai_errors  # type: ignore

            if isinstance(err, genai_errors.ServerError):
                return True  # 5xx すべて一時的扱い
            if isinstance(err, genai_errors.ClientError):
                code = getattr(err, "code", None) or getattr(err, "status_code", None)
                return code == 429
        except ImportError:
            pass
        # anthropic
        try:
            from anthropic import APIStatusError, RateLimitError  # type: ignore

            if isinstance(err, RateLimitError):
                return True
            if isinstance(err, APIStatusError):
                return getattr(err, "status_code", 0) in (502, 503, 504, 529)
        except ImportError:
            pass
        # 文字列ベースのフォールバック (型を動的に取れない環境向け)
        s = str(err).lower()
        return any(
            x in s
            for x in ("503", "unavailable", "502", "504", "rate_limit", "429")
        )

    def _generate_once(self, prompt: str, max_tokens: int = 2048) -> str:
        """1 回だけの呼び出し (リトライなし)。"""
        if self.provider == "gemini":
            resp = self._gemini_client.models.generate_content(
                model=self._gemini_model_name,
                contents=prompt,
            )
            return (resp.text or "").strip()
        else:
            resp = self._client.messages.create(
                model=self._model_name,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            parts = []
            for block in resp.content:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
            return "".join(parts).strip()


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_json(text: str) -> dict:
    """モデル出力から JSON を頑張って取り出す。"""
    text = text.strip()
    # コードフェンス優先
    m = _JSON_FENCE_RE.search(text)
    if m:
        text = m.group(1)
    # 先頭の `{` から末尾の `}` までを抜く
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        text = text[first : last + 1]
    return json.loads(text)


def _score_batch(
    client: AIClient, articles: list[Article], config: dict
) -> list[ScoredArticle]:
    template = _load_prompt("relevance_check")

    payload = []
    for i, a in enumerate(articles):
        body_excerpt = (a.body or a.summary)[:SCORING_BODY_CHARS]
        payload.append(
            {
                "id": i,
                "title": a.title,
                "source": a.source,
                "category": a.category,
                "summary": a.summary[:300],
                "body_excerpt": body_excerpt,
            }
        )

    prompt = _render(
        template,
        {
            "HOLDINGS": _holdings_to_str(config.get("holdings", [])),
            "INTERESTS": _format_list(config.get("interests", [])),
            "EXCLUDES": _format_list(config.get("exclude", [])),
            "ARTICLES_JSON": json.dumps(payload, ensure_ascii=False, indent=2),
        },
    )

    raw = client.generate(prompt, max_tokens=2048)
    try:
        parsed = _extract_json(raw)
    except json.JSONDecodeError as e:
        logger.error("スコア JSON 解析失敗 err=%s raw=%s", e, raw[:500])
        # フォールバック: 全部 5 点にする
        return [
            ScoredArticle(article=a, score=5, reason="スコア解析失敗のため既定値")
            for a in articles
        ]

    results = parsed.get("results") or []
    by_id = {int(r["id"]): r for r in results if "id" in r}

    scored: list[ScoredArticle] = []
    for i, a in enumerate(articles):
        r = by_id.get(i, {})
        score = int(r.get("score", 0))
        score = max(0, min(10, score))
        reason = str(r.get("reason", ""))[:60]
        scored.append(ScoredArticle(article=a, score=score, reason=reason))
    return scored


def score_articles(articles: list[Article], config: dict) -> list[ScoredArticle]:
    """記事をバッチでスコアリング。"""
    if not articles:
        return []
    config = _apply_default_profile(config)
    client = AIClient(config.get("ai_provider", "gemini"))

    scored: list[ScoredArticle] = []
    for i in range(0, len(articles), SCORING_BATCH_SIZE):
        chunk = articles[i : i + SCORING_BATCH_SIZE]
        logger.info("スコアリング中: %d-%d / %d", i, i + len(chunk), len(articles))
        scored.extend(_score_batch(client, chunk, config))
    return scored


# --------------------------------------------------------------------------- #
# Digest generation
# --------------------------------------------------------------------------- #

def _pick_top_and_notable(
    scored: list[ScoredArticle], config: dict
) -> tuple[list[ScoredArticle], list[ScoredArticle]]:
    advanced = config.get("advanced") or {}
    limits = config.get("limits") or {}
    top_threshold = int(advanced.get("score_threshold_top", 7))
    notable_threshold = int(advanced.get("score_threshold_notable", 5))
    top_count = int(limits.get("top_count", 3))
    notable_count = int(limits.get("notable_count", 7))

    sorted_scored = sorted(scored, key=lambda s: s.score, reverse=True)

    top = [s for s in sorted_scored if s.score >= top_threshold][:top_count]
    top_urls = {s.article.url for s in top}
    notable = [
        s
        for s in sorted_scored
        if notable_threshold <= s.score < top_threshold
        and s.article.url not in top_urls
    ][:notable_count]
    return top, notable


def _build_articles_payload(
    top: list[ScoredArticle], notable: list[ScoredArticle]
) -> str:
    payload = []
    for s in top:
        payload.append(_article_for_digest(s, "top"))
    for s in notable:
        payload.append(_article_for_digest(s, "notable"))
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _article_for_digest(s: ScoredArticle, section: str) -> dict:
    a = s.article
    body_excerpt = (a.body or a.summary)[:DIGEST_BODY_CHARS]
    return {
        "section": section,
        "title": a.title,
        "source": a.source,
        "category": a.category,
        "url": a.url,
        "published": a.published.isoformat(),
        "score": s.score,
        "summary": a.summary,
        "body_excerpt": body_excerpt,
    }


def _session_label(now_jst: dt.datetime) -> tuple[str, str]:
    """JST 時刻から (短いラベル, AI への文脈ヒント) を返す。

    朝 (4-12 時) と 夕方 (12-23 時) で内容のフォーカスを切り替える。
    """
    hour = now_jst.hour
    if 4 <= hour < 12:
        return (
            "朝のレポート",
            "今は朝で、米国市場が直前にクローズしました。"
            "米国市場の動向と、本日のアジア・日本市場への影響を中心にまとめてください。",
        )
    else:
        return (
            "夕方のレポート",
            "今は夕方で、日本市場がクローズし、米国市場が開始前です。"
            "日本市場の総括と、これから始まる米国市場で注目すべき材料を中心にまとめてください。",
        )


def build_digest(
    scored: list[ScoredArticle], config: dict, now: dt.datetime | None = None
) -> str:
    """モードに応じたダイジェスト本文を生成。記事ゼロ時はプレースホルダを返す。"""
    if not scored:
        return "📰 Zundamon投資ニュース\n\n今日は注目記事なし。"
    config = _apply_default_profile(config)

    top, notable = _pick_top_and_notable(scored, config)
    if not top and not notable:
        return (
            "📰 Zundamon投資ニュース\n\n"
            "スコア閾値を超える記事が見つかりませんでした。"
            "config.yaml の holdings / interests を見直してみてください。"
        )

    mode: Mode = config.get("mode", "hybrid")
    template = _load_prompt(f"digest_{mode}")

    now_jst = (now or dt.datetime.now(tz=dt.timezone.utc)).astimezone(
        dt.timezone(dt.timedelta(hours=9))
    )
    delivery_str = now_jst.strftime("%Y-%m-%d %H:%M JST")
    session_label, session_context = _session_label(now_jst)

    prompt = _render(
        template,
        {
            "HOLDINGS": _holdings_to_str(config.get("holdings", [])),
            "INTERESTS": _format_list(config.get("interests", [])),
            "DELIVERY_DATETIME": delivery_str,
            "SESSION_LABEL": session_label,
            "SESSION_CONTEXT": session_context,
            "ARTICLES_JSON": _build_articles_payload(top, notable),
        },
    )

    client = AIClient(config.get("ai_provider", "gemini"))
    max_tokens = 3000 if mode == "beginner" else 2000
    text = client.generate(prompt, max_tokens=max_tokens)
    return text.strip() or "📰 Zundamon投資ニュース\n\n(本文生成に失敗しました)"


# --------------------------------------------------------------------------- #
# Convenience
# --------------------------------------------------------------------------- #

def summarize(articles: list[Article], config: dict) -> tuple[str, list[ScoredArticle]]:
    """fetch → score → digest を一気通貫に実行。デバッグ用に scored も返す。"""
    scored = score_articles(articles, config)
    digest = build_digest(scored, config)
    return digest, scored


def _yaml_load_if_exists(path: Path) -> dict | None:
    import yaml

    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


if __name__ == "__main__":  # pragma: no cover
    import sys

    logging.basicConfig(level=logging.INFO)
    # デバッグ実行: サンプル記事をでっち上げてスコア+ダイジェストを試す
    fake = [
        Article(
            source="test",
            category="テスト",
            title="NVDA 決算発表、ガイダンス上方修正",
            url="https://example.com/1",
            published=dt.datetime.now(tz=dt.timezone.utc),
            summary="エヌビディアが決算発表で第2Qガイダンスを上方修正した。",
        )
    ]
    cfg = _yaml_load_if_exists(ROOT_DIR / "config.yaml") or _yaml_load_if_exists(
        ROOT_DIR / "config.yaml.example"
    )
    if not cfg:
        print("config.yaml がありません。config.yaml.example を参考に作成してください。")
        sys.exit(1)
    digest, _ = summarize(fake, cfg)
    print(digest)

"""scripts/fetch.py の最小テスト。

ネットワークに依存しない単体テストのみ。RSS の実取得は E2E 扱い。
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from scripts.fetch import (
    Article,
    _normalize_title,
    dedupe_articles,
    load_sources,
)


ROOT = Path(__file__).resolve().parent.parent


def _make_article(
    title: str,
    url: str,
    minutes_ago: int = 0,
) -> Article:
    pub = dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(minutes=minutes_ago)
    return Article(
        source="test",
        category="test",
        title=title,
        url=url,
        published=pub,
    )


# --------------------------------------------------------------------------- #
# _normalize_title
# --------------------------------------------------------------------------- #

def test_normalize_title_removes_brackets_and_punctuation():
    assert _normalize_title("【速報】エヌビディア、決算発表!") == "速報 エヌビディア 決算発表"


def test_normalize_title_collapses_spaces():
    assert _normalize_title("Hello   World  ") == "hello world"


# --------------------------------------------------------------------------- #
# dedupe_articles
# --------------------------------------------------------------------------- #

def test_dedupe_removes_same_url():
    a1 = _make_article("タイトルA", "https://example.com/a", minutes_ago=10)
    a2 = _make_article("タイトルA 改題", "https://example.com/a", minutes_ago=5)
    result = dedupe_articles([a1, a2])
    assert len(result) == 1


def test_dedupe_removes_similar_titles():
    a1 = _make_article(
        "NVDA decisions announced today",
        "https://example.com/1",
        minutes_ago=10,
    )
    a2 = _make_article(
        "NVDA decisions announced today!",
        "https://example.com/2",
        minutes_ago=5,
    )
    result = dedupe_articles([a1, a2])
    assert len(result) == 1


def test_dedupe_keeps_distinct_titles():
    a1 = _make_article("NVDA 決算好調", "https://example.com/1", minutes_ago=10)
    a2 = _make_article("AAPL サービス部門過去最高", "https://example.com/2", minutes_ago=5)
    result = dedupe_articles([a1, a2])
    assert len(result) == 2


def test_dedupe_prefers_newer_article():
    """同一タイトル扱いされた場合、新しい方が残る。"""
    a_old = _make_article("同じニュース", "https://example.com/old", minutes_ago=60)
    a_new = _make_article("同じニュース", "https://example.com/new", minutes_ago=5)
    result = dedupe_articles([a_old, a_new])
    assert len(result) == 1
    assert result[0].url == "https://example.com/new"


# --------------------------------------------------------------------------- #
# load_sources
# --------------------------------------------------------------------------- #

def test_load_sources_has_entries():
    sources = load_sources(ROOT / "sources.yaml")
    assert isinstance(sources, list)
    assert len(sources) >= 3
    for s in sources:
        assert "name" in s
        assert "url" in s
        assert s["url"].startswith("http")


# --------------------------------------------------------------------------- #
# Article dataclass
# --------------------------------------------------------------------------- #

def test_article_url_hash_is_stable():
    a1 = _make_article("t", "https://example.com/x")
    a2 = _make_article("t", "https://example.com/x")
    assert a1.url_hash == a2.url_hash
    assert len(a1.url_hash) == 16


def test_article_to_dict_serializes_datetime():
    a = _make_article("t", "https://example.com/x")
    d = a.to_dict()
    assert isinstance(d["published"], str)
    # ISO 8601 format sanity
    assert "T" in d["published"]

"""Discord Webhook 配信。

使い方:
    from scripts.deliver import deliver_to_discord
    deliver_to_discord(digest_text)

Discord Embed の description は 4096 文字まで / 1メッセージ合計 6000 文字まで。
長文ダイジェストは複数 embed に分割して送る。
"""

from __future__ import annotations

import logging
import os
import time
from typing import Iterable

import requests

logger = logging.getLogger(__name__)

EMBED_DESC_MAX = 4000  # 4096 までだが安全マージン
EMBED_COLOR = 0x7DD87D  # ずんだ色っぽい緑
RETRY_MAX = 3
RETRY_BASE_SEC = 2


def _chunk_text(text: str, max_len: int = EMBED_DESC_MAX) -> list[str]:
    """行単位で max_len 以下のチャンクに分割。"""
    lines = text.splitlines()
    chunks: list[str] = []
    buf: list[str] = []
    buf_len = 0
    for line in lines:
        # +1 for newline
        add_len = len(line) + 1
        if buf_len + add_len > max_len and buf:
            chunks.append("\n".join(buf))
            buf = [line]
            buf_len = add_len
        else:
            buf.append(line)
            buf_len += add_len
    if buf:
        chunks.append("\n".join(buf))
    return chunks or [""]


def _build_payload(chunks: list[str], title: str | None) -> dict:
    embeds = []
    for i, chunk in enumerate(chunks):
        embed: dict = {
            "description": chunk,
            "color": EMBED_COLOR,
        }
        if i == 0 and title:
            embed["title"] = title
        embeds.append(embed)
    return {
        "username": "Zundamon News Concierge",
        "embeds": embeds,
    }


def _post_with_retry(webhook_url: str, payload: dict) -> None:
    last_err: Exception | None = None
    for attempt in range(1, RETRY_MAX + 1):
        try:
            resp = requests.post(webhook_url, json=payload, timeout=15)
            if resp.status_code == 429:
                # レート制限: Discord が retry_after を JSON で返す
                try:
                    retry_after = float(resp.json().get("retry_after", 1))
                except Exception:
                    retry_after = 2.0
                logger.warning(
                    "Discord rate limited. sleeping %.1fs", retry_after
                )
                time.sleep(retry_after)
                continue
            resp.raise_for_status()
            return
        except requests.RequestException as e:
            last_err = e
            wait = RETRY_BASE_SEC ** attempt
            logger.warning(
                "Webhook POST 失敗 attempt=%d err=%s retry_in=%ds",
                attempt,
                e,
                wait,
            )
            time.sleep(wait)
    raise RuntimeError(f"Discord Webhook 配信に失敗しました: {last_err}")


def deliver_to_discord(
    text: str,
    webhook_url: str | None = None,
    title: str | None = None,
) -> None:
    """Discord に embed で投稿する。

    Args:
        text: 配信本文 (モデル生成済み)
        webhook_url: 省略時は環境変数 DISCORD_WEBHOOK_URL を使用
        title: 先頭 embed のタイトル (任意)
    """
    url = webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        raise RuntimeError(
            "DISCORD_WEBHOOK_URL が未設定です。"
            "GitHub Secrets または .env に設定してください。"
        )

    chunks = _chunk_text(text)
    # Discord は 1 メッセージに embed 10 個まで。長ければ複数メッセージに分ける。
    MAX_EMBEDS_PER_MSG = 10
    for i in range(0, len(chunks), MAX_EMBEDS_PER_MSG):
        msg_chunks = chunks[i : i + MAX_EMBEDS_PER_MSG]
        payload = _build_payload(msg_chunks, title if i == 0 else None)
        _post_with_retry(url, payload)
        logger.info("Discord に %d embed 送信完了", len(msg_chunks))


def deliver_error_notice(message: str, webhook_url: str | None = None) -> None:
    """実行エラー時の簡易通知。失敗しても例外を投げない。"""
    try:
        deliver_to_discord(
            f"⚠️ Zundamon News Concierge エラー\n\n{message[:1500]}",
            webhook_url=webhook_url,
        )
    except Exception as e:
        logger.error("エラー通知すら失敗: %s", e)

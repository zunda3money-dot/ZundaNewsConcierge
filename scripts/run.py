"""Zundamon News Concierge エントリポイント。

通常は GitHub Actions の cron から呼ばれる。ローカル実行も可能:

    python -m scripts.run                  # 本番相当
    python -m scripts.run --dry-run        # 取得+要約のみ、Discord 送信しない
    python -m scripts.run --skip-fetch-body  # 本文取得をスキップ (高速デバッグ)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import traceback
from pathlib import Path

import yaml

from .fetch import fetch_articles, load_sources
from .summarize import build_digest, score_articles
from .deliver import deliver_error_notice, deliver_to_discord
from .deliver_email import deliver_email_error_notice, deliver_to_gmail
from .buy_signals import check_buy_signals, format_signals_block

logger = logging.getLogger("zundamon.run")

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config.yaml"
CONFIG_EXAMPLE_PATH = ROOT_DIR / "config.yaml.example"


def load_config() -> dict:
    path = CONFIG_PATH
    if not path.exists():
        # 最初の起動ではフォールバックとして example を使う (Discord に警告配信)
        if CONFIG_EXAMPLE_PATH.exists():
            logger.warning(
                "config.yaml が未作成のため config.yaml.example を使用します。"
                "必ず config.yaml を作って編集してください。"
            )
            path = CONFIG_EXAMPLE_PATH
        else:
            raise FileNotFoundError(
                "config.yaml も config.yaml.example も見つかりません。"
            )
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    # デフォルト補完
    cfg.setdefault("mode", "hybrid")
    cfg.setdefault("ai_provider", "gemini")
    cfg.setdefault("delivery_time_jst", "06:30")
    cfg.setdefault("holdings", [])
    cfg.setdefault("interests", [])
    cfg.setdefault("exclude", [])
    cfg.setdefault("limits", {"top_count": 3, "notable_count": 7})
    cfg.setdefault(
        "advanced",
        {"score_threshold_top": 7, "score_threshold_notable": 5, "lookback_hours": 24},
    )
    return cfg


def _resolve_email_to(config: dict) -> str | None:
    """email_to を config 優先、なければ環境変数 EMAIL_TO から取得。

    EXPRESS セットアップでは config.yaml を編集せずに Secret EMAIL_TO だけで動く。
    """
    val = (config.get("email_to") or "").strip()
    if val:
        return val
    val = (os.environ.get("EMAIL_TO") or "").strip()
    return val or None


def channels_enabled(config: dict) -> list[str]:
    """環境変数 + config から、有効化されている配信チャネルのリストを返す。

    ルール:
      - DISCORD_WEBHOOK_URL があれば 'discord'
      - GMAIL_FROM + GMAIL_APP_PASSWORD + (config.email_to または環境変数 EMAIL_TO) が揃えば 'email'
    """
    chs: list[str] = []
    if os.environ.get("DISCORD_WEBHOOK_URL"):
        chs.append("discord")
    if (
        os.environ.get("GMAIL_FROM")
        and os.environ.get("GMAIL_APP_PASSWORD")
        and _resolve_email_to(config)
    ):
        chs.append("email")
    return chs


def deliver_all(digest: str, config: dict) -> None:
    """有効化された全チャネルに digest を配信する。

    一部のチャネルが失敗しても他のチャネルへの配信は試みる。
    全失敗時のみ例外を投げる。
    """
    channels = channels_enabled(config)
    if not channels:
        raise RuntimeError(
            "配信チャネルが一つも有効化されていません。"
            "GitHub Secrets に以下のいずれかを設定してください:\n"
            "  - Discord: DISCORD_WEBHOOK_URL\n"
            "  - Email: GMAIL_FROM + GMAIL_APP_PASSWORD + EMAIL_TO"
        )

    errors: list[str] = []
    for ch in channels:
        try:
            if ch == "discord":
                deliver_to_discord(digest)
                logger.info("Discord 配信完了")
            elif ch == "email":
                email_to = _resolve_email_to(config)
                deliver_to_gmail(digest, email_to=email_to)
                logger.info("Email 配信完了 to=%s", email_to)
        except Exception as e:
            logger.error("%s 配信失敗: %s", ch, e)
            errors.append(f"{ch}: {e}")

    if errors and len(errors) == len(channels):
        raise RuntimeError("全チャネル配信失敗: " + "; ".join(errors))
    elif errors:
        logger.warning("一部チャネル失敗: %s", errors)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="zundamon-news-concierge",
        description="毎朝の投資ニュースダイジェストを生成して Discord に配信する",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Discord への配信をスキップし、標準出力にダイジェストを表示",
    )
    p.add_argument(
        "--skip-fetch-body",
        action="store_true",
        help="記事本文の取得をスキップ (RSS summary のみで要約)",
    )
    p.add_argument(
        "--save-raw",
        type=str,
        default=None,
        help="取得 + スコア済みデータを JSON で保存するパス (デバッグ用)",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="デバッグログを有効化",
    )
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    config = load_config()
    lookback = int((config.get("advanced") or {}).get("lookback_hours", 24))

    # 1. Fetch
    logger.info("=== Step 1: RSS 取得 ===")
    sources = load_sources()
    articles = fetch_articles(
        sources=sources,
        lookback_hours=lookback,
        fetch_body=not args.skip_fetch_body,
    )
    logger.info("取得記事数: %d", len(articles))

    if not articles:
        logger.info("記事なし。空メッセージを送信。")
        msg = "📰 Zundamon投資ニュース\n\n今日は該当記事なし。"
        if not args.dry_run:
            deliver_all(msg, config)
        else:
            print(msg)
            print(f"\n--- DRY RUN: 配信先 (送信せず): {channels_enabled(config)} ---")
        return 0

    # 2. Score
    logger.info("=== Step 2: 関連度スコアリング ===")
    scored = score_articles(articles, config)

    if args.save_raw:
        with open(args.save_raw, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in scored], f, ensure_ascii=False, indent=2)
        logger.info("raw dump → %s", args.save_raw)

    # 3. Digest
    logger.info("=== Step 3: ダイジェスト生成 (mode=%s) ===", config.get("mode"))
    digest = build_digest(scored, config)

    # 3.5 買い増しシグナル (config に buy_signals が書かれている場合のみ)
    if config.get("buy_signals"):
        logger.info("=== Step 3.5: 買い増しシグナルチェック ===")
        try:
            signals = check_buy_signals(config)
            block = format_signals_block(signals)
            if block:
                digest = block + "\n" + digest
                logger.info("発動シグナル %d 件をダイジェスト冒頭に挿入", len(signals))
            else:
                logger.info("発動中のシグナルなし")
        except Exception as e:
            # シグナル取得に失敗してもダイジェスト本体は配信する
            logger.warning("買い増しシグナル処理失敗 (本体配信は継続): %s", e)

    # 4. Deliver
    if args.dry_run:
        print("--- DRY RUN: 以下がダイジェスト ---")
        print(digest)
        print(f"\n--- DRY RUN: 配信先 (送信せず): {channels_enabled(config)} ---")
        return 0

    logger.info("=== Step 4: 配信 (チャネル: %s) ===", channels_enabled(config))
    deliver_all(digest, config)
    logger.info("配信完了")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    try:
        return run(args)
    except Exception as e:
        logger.error("実行中に例外発生: %s", e)
        logger.error(traceback.format_exc())
        # 本番実行 (dry-run 以外) では各チャネルにエラー通知
        if not args.dry_run:
            err_msg = f"{type(e).__name__}: {e}"
            if os.environ.get("DISCORD_WEBHOOK_URL"):
                deliver_error_notice(err_msg)
            # config が読めていない可能性もあるので try-except で読む
            try:
                cfg = load_config()
                if cfg.get("email_to") and os.environ.get("GMAIL_APP_PASSWORD"):
                    deliver_email_error_notice(err_msg, email_to=cfg["email_to"])
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(main())

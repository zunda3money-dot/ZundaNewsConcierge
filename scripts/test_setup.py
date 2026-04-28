"""セットアップ検証用の高速チェックスクリプト。

Quest 4-1 で使う。10 秒以内に各 Secret / 設定が正しいか診断して、
ダメなところを ❌ + 具体的な修正案で報告する。

使い方:
    python -m scripts.test_setup

GitHub Actions:
    .github/workflows/test_setup.yml から workflow_dispatch で実行。
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _ok(msg: str) -> None:
    print(f"  ✅ {msg}")


def _ng(msg: str, hint: str = "") -> None:
    print(f"  ❌ {msg}")
    if hint:
        print(f"     💡 {hint}")


def _info(msg: str) -> None:
    print(f"  ℹ️  {msg}")


def check_gemini() -> bool:
    """Gemini API キーが正しく動くかチェック。"""
    print("\n🔧 [1/4] Gemini API キーの検証")
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        _ng(
            "GEMINI_API_KEY が未設定",
            "GitHub Secrets に GEMINI_API_KEY を登録してください "
            "(SETUP_GUIDE Quest 1-2 参照)",
        )
        return False
    if not key.startswith("AIzaSy"):
        _ng(
            "GEMINI_API_KEY の形式が変です (AIzaSy で始まる必要)",
            "AI Studio で発行し直してみてください",
        )
        return False

    try:
        from google import genai

        client = genai.Client(api_key=key)
        # 最小限のリクエストで疎通確認
        resp = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
            contents="OK と一言だけ返してください",
        )
        text = (resp.text or "").strip()
        if not text:
            _ng("Gemini から空の応答", "API キーは認識されましたが応答が空でした")
            return False
        _ok(f"Gemini 疎通成功 (応答: {text[:30]!r})")
        return True
    except Exception as e:
        _ng(
            f"Gemini API 呼び出し失敗: {e}",
            "API キーが古い/無効な可能性。AI Studio で再発行してください",
        )
        return False


def check_discord() -> bool | None:
    """Discord Webhook が動くかチェック (未設定時はスキップ)。"""
    print("\n📨 [2/4] Discord Webhook の検証")
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        _info("DISCORD_WEBHOOK_URL 未設定 → Discord 配信はスキップ")
        return None
    if not url.startswith("https://discord.com/api/webhooks/"):
        _ng(
            "DISCORD_WEBHOOK_URL の形式が変です",
            "https://discord.com/api/webhooks/... で始まる URL を貼ってください",
        )
        return False

    try:
        import requests

        resp = requests.post(
            url,
            json={"content": "✅ セットアップ確認: Discord Webhook OK です"},
            timeout=15,
        )
        if resp.status_code in (200, 204):
            _ok("Discord Webhook 疎通成功 (テストメッセージ送信)")
            return True
        _ng(
            f"Discord 応答 status={resp.status_code}",
            "URL が削除されたチャンネル/サーバーを指している可能性。再発行してください",
        )
        return False
    except Exception as e:
        _ng(f"Discord 送信失敗: {e}", "ネットワーク or URL 不正")
        return False


def check_email() -> bool | None:
    """Gmail SMTP の認証 + テスト送信 (未設定時はスキップ)。"""
    print("\n✉️  [3/4] Gmail (SMTP) の検証")
    email_from = os.environ.get("GMAIL_FROM")
    app_pw = os.environ.get("GMAIL_APP_PASSWORD")
    email_to = os.environ.get("EMAIL_TO")

    # config.yaml にも email_to があるかチェック
    if not email_to:
        try:
            import yaml

            cfg_path = Path(__file__).resolve().parent.parent / "config.yaml"
            if cfg_path.exists():
                with cfg_path.open("r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                email_to = (cfg.get("email_to") or "").strip()
        except Exception:
            pass

    if not email_from and not app_pw and not email_to:
        _info("Gmail 関連 Secret 未設定 → メール配信はスキップ")
        return None
    missing = []
    if not email_from:
        missing.append("GMAIL_FROM")
    if not app_pw:
        missing.append("GMAIL_APP_PASSWORD")
    if not email_to:
        missing.append("EMAIL_TO (または config.yaml の email_to)")
    if missing:
        _ng(
            f"Gmail 関連の不足: {', '.join(missing)}",
            "SETUP_GUIDE Quest 1-3b / 1-4b / 2-2 参照",
        )
        return False

    try:
        from .deliver_email import deliver_to_gmail

        deliver_to_gmail(
            "✅ セットアップ確認テスト\n\n"
            "このメールが届いていれば、Gmail 配信の設定は完璧です。\n"
            "明日朝 06:00 から自動配信が始まります。",
            email_to=email_to,
            subject="✅ Zundamon News - セットアップ確認 OK",
        )
        _ok(f"Gmail 送信成功 (to={email_to})")
        return True
    except Exception as e:
        _ng(
            f"Gmail 送信失敗: {e}",
            "アプリパスワードが正しいか、2段階認証が ON か再確認 "
            "(https://myaccount.google.com/apppasswords)",
        )
        return False


def check_config() -> bool:
    """config.yaml の存在・読み込み・最低限のチェック。"""
    print("\n⚙️  [4/4] config 設定の確認")
    try:
        from .run import load_config

        cfg = load_config()
    except Exception as e:
        _ng(f"config 読み込み失敗: {e}", "リポジトリのルートで実行してください")
        return False

    holdings = cfg.get("holdings") or []
    interests = cfg.get("interests") or []
    if not holdings and not interests:
        _info(
            "holdings も interests も未設定 → "
            "一般市場ニュース (S&P500/NASDAQ/新NISA等) のデフォルトで動きます"
        )
    else:
        _ok(
            f"プロファイル設定済 (holdings={len(holdings)} 銘柄 / "
            f"interests={len(interests)} キーワード)"
        )

    mode = cfg.get("mode", "hybrid")
    _ok(f"モード: {mode}")
    return True


def main() -> int:
    logging.basicConfig(level=logging.WARNING)  # チェック出力以外はノイズに
    print("=" * 60)
    print("🩺 Zundamon News Concierge セットアップ確認")
    print("=" * 60)

    results: dict[str, bool | None] = {}
    results["Gemini"] = check_gemini()
    results["Discord"] = check_discord()
    results["Email"] = check_email()
    results["Config"] = check_config()

    print("\n" + "=" * 60)
    print("📊 結果サマリー")
    print("=" * 60)
    for name, ok in results.items():
        if ok is None:
            print(f"  {name:8s}: ⏭  スキップ")
        elif ok:
            print(f"  {name:8s}: ✅ OK")
        else:
            print(f"  {name:8s}: ❌ NG")

    # 最低限「Gemini OK」 + 「Discord か Email のどちらか OK」が必要
    gemini_ok = results["Gemini"] is True
    delivery_ok = results["Discord"] is True or results["Email"] is True
    config_ok = results["Config"] is True

    print()
    if gemini_ok and delivery_ok and config_ok:
        print("🎉 すべての必須項目 OK! 明日の配信を待ちましょう。")
        return 0
    else:
        print("⚠️  ❌ の項目を解決してから再度このワークフローを実行してください。")
        if not delivery_ok:
            print(
                "    必須: DISCORD_WEBHOOK_URL または "
                "(GMAIL_FROM + GMAIL_APP_PASSWORD + EMAIL_TO) のいずれかが必要です。"
            )
        return 1


if __name__ == "__main__":
    sys.exit(main())

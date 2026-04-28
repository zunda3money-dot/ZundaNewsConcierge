"""Gmail SMTP 経由でダイジェストをメール配信するモジュール。

Gmail の「アプリパスワード」(16 桁の専用パスワード) を使う。
通常の Google ログインパスワードは使えない (2024 年以降 SMTP では拒否される)。

アプリパスワード発行: https://myaccount.google.com/apppasswords
  ※事前に 2 段階認証を ON にする必要あり (https://myaccount.google.com/security)

公開 API:
    deliver_to_gmail(text, subject=..., email_to=..., html=None)
    deliver_email_error_notice(message)
"""

from __future__ import annotations

import datetime as dt
import html as html_lib
import logging
import os
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 465  # SSL


def _get_creds() -> tuple[str, str]:
    email_from = os.environ.get("GMAIL_FROM")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not email_from:
        raise RuntimeError(
            "GMAIL_FROM が未設定です (送信元 Gmail アドレス)。"
            "GitHub Secrets / .env に追加してください。"
        )
    if not app_password:
        raise RuntimeError(
            "GMAIL_APP_PASSWORD が未設定です (Gmail アプリパスワード 16 桁)。"
            "発行方法: https://myaccount.google.com/apppasswords"
        )
    # アプリパスワードはスペース区切りで提示されるが、登録時にスペース有無どちらも許容する
    app_password = app_password.replace(" ", "")
    return email_from, app_password


def _digest_to_html(text: str) -> str:
    """プレーンテキストの digest を、メールクライアントで読みやすい HTML に変換。"""
    escaped = html_lib.escape(text)
    # URL を <a> タグに
    escaped = re.sub(
        r"(https?://[^\s<]+)",
        r'<a href="\1" style="color:#1a73e8;text-decoration:none;">\1</a>',
        escaped,
    )
    # 行頭の絵文字付きセクション見出し (🔥 必読 / 📊 その他注目) を強調
    escaped = re.sub(
        r"^(🔥[^\n]+|📊[^\n]+)$",
        r'<div style="font-size:1.1em;font-weight:bold;margin-top:1em;">\1</div>',
        escaped,
        flags=re.MULTILINE,
    )
    # 行頭の 📰 タイトル行を更に強調
    escaped = re.sub(
        r"^(📰[^\n]+)$",
        r'<h2 style="color:#2e7d32;margin:0 0 .5em 0;">\1</h2>',
        escaped,
        flags=re.MULTILINE,
    )
    # 改行を <br> に
    escaped = escaped.replace("\n", "<br>\n")
    return f"""<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="font-family: -apple-system, 'Segoe UI', 'Hiragino Sans', sans-serif; line-height:1.7; color:#222; max-width:680px; margin:0 auto; padding:1.5em;">
{escaped}
<hr style="border:none;border-top:1px solid #ddd;margin-top:2em;">
<p style="color:#888;font-size:.85em;">
  このメールは Zundamon News Concierge (オープンソース) から自動送信されています。<br>
  配信を停止したい場合は GitHub の Settings &gt; Actions から workflow を無効化してください。
</p>
</body></html>"""


def _build_subject(digest_text: str, fallback_dt: dt.datetime | None = None) -> str:
    """digest 本文からセッション情報を抜いて subject を組み立てる。"""
    fallback_dt = fallback_dt or dt.datetime.now(
        tz=dt.timezone(dt.timedelta(hours=9))
    )
    # 1 行目に session label が入っている想定: 📰 Zundamon投資ニュース (朝のレポート) [...]
    first_line = digest_text.split("\n", 1)[0]
    m = re.search(r"\(([^)]+)\)", first_line)
    session = m.group(1) if m else ""
    date_part = fallback_dt.strftime("%Y-%m-%d")
    if session:
        return f"📰 Zundamon News - {session} {date_part}"
    return f"📰 Zundamon News - {date_part}"


def deliver_to_gmail(
    text: str,
    *,
    email_to: str,
    subject: str | None = None,
    html: str | None = None,
) -> None:
    """指定の Gmail/外部メールアドレスにダイジェストを送信。

    Args:
        text: プレーンテキストの digest
        email_to: 送信先メールアドレス (config.yaml の email_to 由来)
        subject: 件名。省略時は digest から自動組み立て
        html: HTML 本文。省略時は text から _digest_to_html() で自動生成
    """
    if not email_to:
        raise RuntimeError(
            "送信先 (config.yaml の email_to) が未設定です。"
        )
    email_from, app_password = _get_creds()

    if subject is None:
        subject = _build_subject(text)
    if html is None:
        html = _digest_to_html(text)

    msg = MIMEMultipart("alternative")
    msg["From"] = f"Zundamon News Concierge <{email_from}>"
    msg["To"] = email_to
    msg["Subject"] = subject
    # multipart/alternative では plain → html の順で添付するのが規約
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(
            GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, context=context, timeout=20
        ) as server:
            server.login(email_from, app_password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(
            f"Gmail 認証失敗: {e}\n"
            "アプリパスワードが正しいか、2 段階認証が有効か確認してください。\n"
            "発行方法: https://myaccount.google.com/apppasswords"
        ) from e
    except (smtplib.SMTPException, OSError) as e:
        raise RuntimeError(f"Gmail 送信失敗: {e}") from e

    logger.info("Gmail 送信完了: from=%s to=%s", email_from, email_to)


def deliver_email_error_notice(
    message: str, email_to: str | None = None
) -> None:
    """実行エラー時の簡易通知。失敗しても例外を投げない。"""
    try:
        if not email_to:
            return
        deliver_to_gmail(
            f"⚠️ Zundamon News Concierge 実行エラー\n\n{message[:1500]}",
            email_to=email_to,
            subject="⚠️ Zundamon News - 実行エラー",
        )
    except Exception as e:
        logger.error("メールでのエラー通知に失敗: %s", e)

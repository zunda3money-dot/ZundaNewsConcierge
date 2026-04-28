"""買い増しシグナル: ユーザーが冷静なときに設定したルールが満たされたかチェックする。

⚠️ 重要 (規制リスク回避):
    本モジュールは「投資判断の助言」を行うものではありません。
    「ユーザーが事前に config.yaml に書いた条件式」が満たされたことを
    機械的に通知するだけです。プロンプト・出力ともに「買い」「売り」を
    推奨する語彙は禁止し、必ず「あなたが事前設定したルールが満たされた」
    という表現を使ってください。

データソース:
    yfinance (Yahoo Finance の非公式 SDK、無料、API キー不要)。
    取得失敗時はそのシグナルだけスキップして他は処理続行 (graceful degradation)。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BuySignal:
    ticker: str
    target_below: float
    current_price: float
    note: str = ""
    currency: str = ""

    @property
    def triggered(self) -> bool:
        return self.current_price <= self.target_below

    @property
    def discount_pct(self) -> float:
        """設定ライン比、現在値の割安度 (%)。負ならライン超過、正ならライン未満。"""
        if self.target_below <= 0:
            return 0.0
        return (self.target_below - self.current_price) / self.target_below * 100

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "target_below": self.target_below,
            "current_price": self.current_price,
            "discount_pct": self.discount_pct,
            "note": self.note,
            "currency": self.currency,
        }


# --------------------------------------------------------------------------- #
# Price fetching
# --------------------------------------------------------------------------- #

def fetch_current_price(ticker: str) -> tuple[float | None, str]:
    """ticker の現在価格と通貨を取得。失敗時 (None, '')。

    yfinance のヒストリ最新終値ベース。日中は前日終値となるが、
    ルール判定には十分。日本株は ticker に `.T` を付ける (例: 7203.T)。
    """
    try:
        import yfinance as yf

        t = yf.Ticker(ticker)
        # info はネットワーク的に重いので history 1 件で済ませる
        hist = t.history(period="2d", auto_adjust=False)
        if hist.empty:
            logger.warning("ヒストリ空: %s", ticker)
            return None, ""
        price = float(hist["Close"].iloc[-1])
        currency = ""
        try:
            # info は呼べる場合のみ通貨を取る (失敗しても本体は OK)
            currency = (t.fast_info.get("currency") or "").upper()
        except Exception:
            pass
        return price, currency
    except Exception as e:
        logger.warning("価格取得失敗 ticker=%s err=%s", ticker, e)
        return None, ""


# --------------------------------------------------------------------------- #
# Rule evaluation
# --------------------------------------------------------------------------- #

def check_buy_signals(config: dict) -> list[BuySignal]:
    """config の buy_signals 設定をチェック。

    config.yaml 例:
        buy_signals:
          - ticker: NVDA
            target_below: 110.0
            note: "本格買い増しライン"
          - ticker: 7203.T
            target_below: 2500
            note: "押し目"

    Returns:
        ルールが**発動した** (current_price <= target_below) シグナルだけのリスト。
        ヒストリ取得失敗のシグナルはスキップ (致命的にしない)。
    """
    rules = config.get("buy_signals") or []
    if not rules:
        return []

    triggered: list[BuySignal] = []
    for r in rules:
        ticker = (r.get("ticker") or "").strip()
        target = r.get("target_below")
        note = (r.get("note") or "").strip()
        if not ticker or target is None:
            continue
        try:
            target = float(target)
        except (TypeError, ValueError):
            logger.warning("target_below が数値ではない: %s = %r", ticker, target)
            continue

        price, currency = fetch_current_price(ticker)
        if price is None:
            continue

        sig = BuySignal(
            ticker=ticker,
            target_below=target,
            current_price=price,
            note=note,
            currency=currency,
        )
        if sig.triggered:
            logger.info(
                "ルール発動: %s 現在 %.2f%s ≤ ライン %.2f (-%.1f%%)",
                ticker,
                price,
                f" {currency}" if currency else "",
                target,
                sig.discount_pct,
            )
            triggered.append(sig)
        else:
            logger.debug(
                "ルール未発動: %s 現在 %.2f > ライン %.2f", ticker, price, target
            )
    return triggered


# --------------------------------------------------------------------------- #
# Formatting (digest 冒頭に挿入する Markdown ブロック)
# --------------------------------------------------------------------------- #

def format_signals_block(signals: list[BuySignal]) -> str:
    """ダイジェスト冒頭に prepend するブロック。発動ゼロなら空文字。

    EP19 で目立つよう、独立セクションとして強調表示。
    """
    if not signals:
        return ""

    lines = [
        "🎯 **ルール発動: あなたが事前設定したラインに到達しました**",
        "",
    ]
    for s in signals:
        cur_str = f" {s.currency}" if s.currency else ""
        note_str = f" — {s.note}" if s.note else ""
        # 価格は通貨に応じて桁数調整: JPY は整数、それ以外 (USD等) は小数 2 桁
        if s.currency.upper() == "JPY":
            price_fmt = f"{s.current_price:,.0f}"
            target_fmt = f"{s.target_below:,.0f}"
        else:
            price_fmt = f"{s.current_price:,.2f}"
            target_fmt = f"{s.target_below:,.2f}"
        lines.append(
            f"  【{s.ticker}】現在 {price_fmt}{cur_str} ＜ 設定ライン {target_fmt}{cur_str}"
            f" (ライン比 {s.discount_pct:+.1f}%){note_str}"
        )

    lines.extend(
        [
            "",
            "ℹ️ これは投資助言ではありません。あなたが**冷静なときに事前設定したルール**が",
            "  満たされたことを通知しています。判断はご自身で行ってください。",
            "─" * 30,
            "",
        ]
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI (デバッグ用)
# --------------------------------------------------------------------------- #

def _cli() -> None:
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    from .run import load_config

    config = load_config()
    signals = check_buy_signals(config)
    if not signals:
        print("発動中のシグナルはありません。")
        sys.exit(0)
    print(format_signals_block(signals))


if __name__ == "__main__":
    _cli()

"""ポートフォリオ画像から config.yaml を自動生成する開発者ツール。

⚠️ 想定ユーザー:
    - 主本人 (EP19 デモ録画用、ローカル実行)
    - GitHub Codespaces で完結したい中級者
    - Python 環境を持っている開発者
    - 画像を Gemini API 経由で送りたい人 (有料 API 経由は学習に使われない)

⚠️ 一般視聴者向けではありません。
    Python 環境不要のお手軽ルートは SETUP_GUIDE.md の Quest 3-1 を参照。
    視聴者は AI Studio (https://aistudio.google.com/) のブラウザチャットで
    同じことができます (画像を貼って prompts/config_from_image.md のプロンプトを送るだけ)。

使い方:
    python -m scripts.config_from_image path/to/portfolio.png
    python -m scripts.config_from_image path/to/portfolio.png --output config.yaml
    python -m scripts.config_from_image path/to/portfolio.png --mode beginner

入力対応形式:
    .png / .jpg / .jpeg / .webp
    SBI証券、楽天証券、マネックス、Apple Stocks、TradingView 等の
    ポートフォリオ表示スクショなら何でも

出力:
    YAML テキストを stdout (または --output 指定先) に書き出す。
    そのまま config.yaml としてリポジトリに置けば動く。

⚠️ 注意:
    AI が画像から読み取った内容を**目視で必ず確認**してから運用してください。
    特に保有銘柄の抜け漏れ・誤読 (NVDA を NVD にしている等) は致命的です。
"""

from __future__ import annotations

import argparse
import logging
import mimetypes
import os
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT_DIR / "prompts" / "config_from_image.md"


def _detect_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime is None:
        # 拡張子で雑にフォールバック
        ext = path.suffix.lower()
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }.get(ext, "image/png")
    return mime


def _strip_yaml_fence(text: str) -> str:
    """モデルがコードフェンスを付けてしまった場合に剥がす。"""
    text = text.strip()
    m = re.match(r"^```(?:ya?ml)?\s*\n(.*?)\n```\s*$", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text


def generate_config_from_image(
    image_path: Path,
    mode_override: str | None = None,
) -> str:
    """画像 1 枚から config.yaml テキストを生成して返す。"""
    if not image_path.exists():
        raise FileNotFoundError(f"画像が見つかりません: {image_path}")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY が設定されていません。"
            "AI Studio (https://aistudio.google.com/) で取得し、"
            "環境変数または .env に設定してください。"
        )

    from google import genai
    from google.genai import types

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    if mode_override:
        prompt += f"\n\n## 追加指示\n\n出力の `mode:` は `{mode_override}` 固定にしてください。\n"

    image_bytes = image_path.read_bytes()
    mime = _detect_mime(image_path)
    logger.info("画像読み込み: %s (%s, %d bytes)", image_path, mime, len(image_bytes))

    client = genai.Client(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    logger.info("Gemini (%s) に画像 + プロンプトを送信中...", model_name)
    resp = client.models.generate_content(
        model=model_name,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime),
            prompt,
        ],
    )
    text = (resp.text or "").strip()
    if not text:
        raise RuntimeError("Gemini から空の応答が返りました")

    return _strip_yaml_fence(text)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="config_from_image",
        description="ポートフォリオ画像から config.yaml を自動生成",
    )
    p.add_argument("image", type=str, help="ポートフォリオ画像のパス (.png/.jpg/.webp)")
    p.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="出力先 (省略時は stdout)",
    )
    p.add_argument(
        "--mode",
        choices=["beginner", "expert", "hybrid"],
        default=None,
        help="出力の mode を強制指定 (省略時は AI が選ぶ)",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="デバッグログを有効化",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    image_path = Path(args.image).resolve()
    try:
        yaml_text = generate_config_from_image(image_path, mode_override=args.mode)
    except Exception as e:
        logger.error("生成失敗: %s", e)
        return 1

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(yaml_text + "\n", encoding="utf-8")
        logger.info("書き出し完了: %s", out_path)
    else:
        print(yaml_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

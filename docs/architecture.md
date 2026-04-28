# 🏗 アーキテクチャ設計

このドキュメントは、**Zundamon 投資ニュースコンシェルジュ** の内部構造と設計判断を記録したものです。

**対象読者**:
- コードを読みたい/改変したい中級以上のユーザー
- 別ドメイン (ゲーム情報、副業等) に転用したい開発者
- AI コーディングエージェント (将来の機能拡張で SPEC と合わせて読む)

---

## 1. 全体フロー

```
                                         ┌─────────────────────────┐
                                         │  GitHub Actions (cron)  │
                                         │  schedule: 30 21 * * *  │
                                         └───────────┬─────────────┘
                                                     │ 毎朝 06:30 JST
                                                     ▼
                                         ┌─────────────────────────┐
                                         │    scripts/run.py       │
                                         │  (オーケストレータ)       │
                                         └───────────┬─────────────┘
                                                     │
            ┌────────────────────────────────────────┼────────────────────────────────────────┐
            ▼                                        ▼                                        ▼
┌───────────────────────┐              ┌───────────────────────┐              ┌───────────────────────┐
│  1. scripts/fetch.py  │              │ 2. scripts/summarize  │              │ 3. scripts/deliver.py │
│  ─────────────────    │              │ ─────────────────     │              │ ─────────────────     │
│  • RSS 5 feeds 取得    │              │  • バッチ関連度スコア  │              │  • Discord Webhook    │
│  • 過去 N 時間フィルタ   │   Article[]  │  • top/notable 仕分け │   digest str  │  • Embed 分割送信      │
│  • 本文取得             │─────────────>│  • モード別 digest 生成│─────────────>│  • 429 retry/backoff   │
│  • URL/タイトル重複除去  │              │                      │               │                       │
└───────────────────────┘              └──────────┬────────────┘              └──────────────────────┘
            ▲                                     │
            │                                     ▼
┌───────────────────────┐              ┌───────────────────────┐
│    sources.yaml       │              │    prompts/*.md       │
│  (RSS フィード一覧)     │              │   (4 種のプロンプト)    │
└───────────────────────┘              └───────────────────────┘
                                                  ▲
                                                  │
                                       ┌──────────┴────────────┐
                                       │    config.yaml        │
                                       │  (holdings/interests) │
                                       └───────────────────────┘
```

---

## 2. レイヤー別責務

### L1: I/O 層 (fetch.py / deliver.py)

**fetch.py**
- RSS フィードから `feedparser` でエントリを抽出
- 過去 24h (config から可変) のみ残す
- 記事本文を `requests` + `BeautifulSoup` で取得 (失敗しても止めない)
- `chardet` で文字化け対策
- URL ハッシュ (sha256 16 文字) とタイトル Levenshtein 距離で重複除去

**deliver.py**
- Discord Webhook に Rich Embed 形式で POST
- description は 1 embed 4096 字制限 → 行単位で分割
- 1 メッセージ 10 embed 制限を超えたら複数メッセージに分割
- 429 Too Many Requests → `retry_after` ヘッダに従って sleep
- その他 HTTP エラー → 指数バックオフで最大 3 回リトライ

### L2: AI 層 (summarize.py)

**`AIClient` ラッパ**
- `provider in {"gemini", "claude"}` で分岐
- `.generate(prompt, max_tokens)` の統一インターフェース
- API キーは `os.environ` から取得 (インスタンス化時にチェック)
- モデル名は `GEMINI_MODEL` / `ANTHROPIC_MODEL` 環境変数で上書き可

**スコアリング (`score_articles`)**
- 20 件/バッチで AI に投げる (長大 prompt 回避)
- JSON 応答を `_extract_json` でロバストにパース (コードフェンス剥がし、最初の `{` ～ 最後の `}` 抽出)
- 解析失敗時はフォールバック (全記事スコア 5) で配信を止めない

**ダイジェスト生成 (`build_digest`)**
- `config.advanced.score_threshold_{top,notable}` でソート + 仕分け
- モードに応じた `prompts/digest_{mode}.md` を選択
- AI に渡す本文は 1500 字までに切り詰め (API コスト抑制)

### L3: オーケストレーション層 (run.py)

- `load_config()` → `fetch_articles()` → `score_articles()` → `build_digest()` → `deliver_to_discord()`
- 例外は最上層でキャッチ、Discord にエラー通知を送る (ユーザーが気づける)
- CLI 引数:
  - `--dry-run`: Discord 送信スキップ、stdout に出す
  - `--skip-fetch-body`: 本文取得スキップ (高速デバッグ)
  - `--save-raw`: スコア付き全記事を JSON ダンプ

### L4: 実行基盤 (.github/workflows/daily.yml)

- `on.schedule.cron: '30 21 * * *'` (06:30 JST)
- `on.workflow_dispatch`: GitHub UI から手動実行ボタン
- `runs-on: ubuntu-latest`, `timeout-minutes: 10`
- Secrets を env に流し込んで `python -m scripts.run`

---

## 3. 設計判断の記録

### Q. なぜ GitHub Actions で実行するのか?

- ユーザーの PC を起動する必要がないこと (視聴者層の生活パターンに合わない朝一のPC起動要求を回避)
- 無料枠で十分: 1 日 1 回・1 分弱の実行なので公開リポジトリの 2000 分/月 に入る (Private でも 2000 分/月)
- Secrets 管理が組み込みで安全
- 別プラットフォーム (n8n, Zapier, Heroku 等) 依存を避けて「GitHub だけ知ってれば OK」に

### Q. なぜ feedparser で自作し、既存OSS (Horizon, auto-news 等) をフォークしなかったか?

- 既存 OSS は機能過多で非エンジニアには複雑
- コア処理が **300 行程度で自作可能**
- 自作した方が SPEC 通りのプロンプト外部化 / モード切替 / YAML 中心の設計をストレートに実装できる

### Q. なぜ Gemini をデフォルトにしたか?

- 視聴者が**無料で使えること**が最優先 (EP19 の配布コンセプト)
- Google アカウントさえあれば API キー発行可 (OpenAI や Anthropic はクレカ必須)
- 品質は Claude > Gemini だが、ニュース要約レベルでは Gemini Flash でも十分

### Q. なぜ 3 モード (beginner/expert/hybrid) に分けたか?

- 初心者と上級者の情報ニーズがまったく違う
- 初心者: 「この記事自分にとって何なの?」を丁寧に説明してほしい
- 上級者: 「数値だけくれ」
- ハイブリッドは両立させた**デフォルトおすすめ**

### Q. なぜプロンプトを `prompts/*.md` に外部化したか?

- AI の出力品質は**プロンプトで 8 割決まる**
- エンジニアでないユーザーでも Markdown ファイルなら編集できる
- モデル (Gemini/Claude) を切り替えたときのプロンプト微調整がしやすい
- バージョン管理で「改善の履歴」を残せる

### Q. なぜ config は YAML なのか?

- JSON よりコメントが書ける (非エンジニアへの説明重要)
- TOML よりネスト構造が素直
- GitHub UI 上で直接編集できる
- `PyYAML` という定番ライブラリがある

### Q. なぜ重複除去を URL ハッシュ + Levenshtein の 2 段階にしたか?

- **URL ハッシュだけ**: 同じ記事でも転載元 URL が違うと別記事扱いになる (Bloomberg → Reuters 転載等)
- **タイトル完全一致**: 句読点違い・半角全角違いで漏れる
- Levenshtein 距離 (類似度 0.85 以上) で「ほぼ同一タイトル」を吸収

### Q. なぜスコアリング閾値は top=7, notable=5 なのか?

- 0〜10 のスケールで、
  - **10**: 保有銘柄の決算・M&A 等の最重要 → 必ず top
  - **7〜9**: 保有銘柄関連・セクターニュース → top 候補
  - **5〜6**: 興味分野の記事 → notable
  - **<5**: マクロすぎる / 関連性薄い → 切り捨て
- 運用しながら `config.yaml.advanced` で各自調整できるようにしている

---

## 4. データが**保存されない**設計

本ツールは **stateless**。過去の記事履歴や送信履歴をファイルに保存しません。

**理由**:
- GitHub Actions の ephemeral な実行環境で永続化するには Storage (S3 / GitHub Releases / Git commit) が必要 → 複雑化
- RSS 側の過去 24h フィルタで「同じ記事を2回送ること」は実運用上ほぼ起きない
- 非エンジニアに「履歴 DB の操作」を強いるのは UX に反する

**副作用**: ごく稀に、RSS 発行遅延で 24h 境界を跨いだ記事が 2 日連続で届くことがある。許容範囲と判断。

---

## 5. 拡張ポイント

別ドメイン (ゲーム / 副業 / 節税 / 趣味) に転用する場合、以下を差し替えるだけで良い設計にしてあります:

| 差し替えるもの | どこ |
|---|---|
| RSS ソース | `sources.yaml` |
| ユーザープロファイル項目 | `config.yaml` + `prompts/relevance_check.md` |
| ダイジェスト表示フォーマット | `prompts/digest_{mode}.md` |
| 配信先 (Discord 以外) | `scripts/deliver.py` に新しい関数追加 + `run.py` で切替 |

**変えずに済むもの**:
- `scripts/fetch.py` (RSS 仕様準拠なら無変更)
- `scripts/summarize.py` の `AIClient` 抽象
- GitHub Actions ワークフロー構造

---

## 6. セキュリティ考慮

- **API キー**: `os.environ` 経由のみ。コードにハードコードしない。`.gitignore` に `config.yaml` / `.env` / `*.key` / `secrets.yaml`
- **保有銘柄情報**: Private リポジトリに閉じれば外部に漏れない。SETUP_GUIDE で Private を明示的に推奨
- **Webhook URL**: GitHub Secrets 経由のみ。ログにも出ないよう注意
- **依存関係**: 使用パッケージは最小限、業界標準のみ (feedparser, requests, yaml, AI 公式 SDK)

---

## 7. パフォーマンス実測値 (想定)

| 処理 | 所要時間 |
|---|---|
| RSS 取得 (5 フィード + 本文取得) | 20〜40 秒 |
| AI スコアリング (20 記事) | 5〜10 秒 |
| ダイジェスト生成 | 3〜8 秒 |
| Discord 送信 | 1〜2 秒 |
| **合計** | **30〜60 秒** |

GitHub Actions の `timeout-minutes: 10` に十分収まる。

---

## 8. 将来の変更時の注意

- **RSS URL が消失した場合**: `sources.yaml` から該当行を削除するだけ。他のフィードはそのまま動く (`_fetch_feed` は例外を catch してスキップする)
- **モデル名が変わった場合**: `AIClient._init_gemini` / `_init_claude` のデフォルトモデル名を更新。`GEMINI_MODEL` / `ANTHROPIC_MODEL` 環境変数でも上書き可
- **Discord Webhook API 仕様変更**: `scripts/deliver.py::_post_with_retry` のみ修正

---

## 関連ドキュメント

- [SPEC.md](../SPEC.md) - 全体要件定義
- [prompts_design.md](./prompts_design.md) - プロンプト設計の意図
- [SETUP_GUIDE.md](../SETUP_GUIDE.md) - ユーザー向けセットアップ

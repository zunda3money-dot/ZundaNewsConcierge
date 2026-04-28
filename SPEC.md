# Zundamon 投資ニュースコンシェルジュ - 完全スペック文書

**作成日**: 2026-04-24
**バージョン**: v0.1 (実装前スペック)
**対象読者**: この文書を読んで実装を担当する Claude Code セッション (新規セッション推奨)

---

## 🎯 プロジェクト目的

「ずんだもんの三刀流マネーラボ」チャンネルの視聴者が、**毎朝GitHub上で動く自分専用のAI投資ニュース秘書**を**完全無料で**持てるようにするツール。動画 EP19 で紹介・配布する想定。

### 差別化の核
- **非エンジニア向け**: コードを1行も書かせない。Python知らなくても使える
- **ゲーミフィケーション**: SETUP_GUIDE をクエスト形式にして楽しい体験に
- **初心者/上級者モード切替**: 投資初心者も上級者も満足できるハイブリッドデフォルト
- **オンライン完結**: GitHub Actions で走るからユーザーのPCは不要

---

## 👥 想定ユーザー層

### Primary (視聴者・配布される人)
- **属性**: 20-40代会社員、投資始めたばかり〜中級者
- **PC スキル**: Google検索ができる、パスワード管理ができる、コピペができる
- **コーディング経験**: なし、あるいはHTML齧った程度
- **目的**: 毎朝の投資情報収集を自動化したい、でも複雑な設定は嫌だ

### Secondary (運営者・主本人)
- **属性**: ずんだもんの三刀流マネーラボ主
- **既存ツール**: Claude Code Max契約 ($100/月)
- **本ツール用**: Claude Haiku or Gemini Flash API別契約 (月300-500円想定)
- **環境**: 朝一にPCを起動する生活パターン、個人PC常用

---

## 🏗 技術スタック (決定事項)

| 項目 | 採用 | 理由 |
|---|---|---|
| 言語 | Python 3.11+ | RSS処理とAI API呼び出しに最適 |
| RSS パーサ | `feedparser` | 業界標準 |
| デフォルトAI | Google Gemini Flash (無料枠) | Google アカウントのみで利用可、無料、十分な品質 |
| オプションAI | Anthropic Claude Haiku ($0.01-0.05/日) | 既存Claudeユーザー向け、高品質 |
| 配信先 | Discord Webhook | 非エンジニア最易、LINE Notify廃止のため |
| 実行基盤 | GitHub Actions (cron) | ユーザーPC不要、公開repo無料枠で十分 |
| 設定管理 | `config.yaml` (GitHub UI編集) | Python知らなくてもブラウザで編集可 |
| 秘密情報 | GitHub Secrets | API キー・Webhook URL の安全管理 |

### 非採用 (理由)
- ❌ LINE Notify: 2025年に公式サービス終了
- ❌ LINE Messaging API: 設定が複雑で非エンジニア向きではない
- ❌ Telegram: 日本ユーザー層が薄い
- ❌ n8n / Zapier: 別プラットフォームに依存するUX複雑化
- ❌ 既存OSS (Horizon, auto-news, etc.) のフォーク: 機能過多で初心者向きでない。独自実装でシンプル化

---

## 🎨 機能仕様

### A. 情報取得 (fetch.py)

`sources.yaml` に定義された RSS フィードから全記事を取得。

**v1.0 対応ソース (全て無料)**:
```yaml
sources:
  - name: Bloomberg Japan - Top
    url: https://assets.wor.jp/rss/rdf/bloomberg/top.rdf
    category: 総合
  - name: Bloomberg Japan - Markets
    url: https://assets.wor.jp/rss/rdf/bloomberg/markets.rdf
    category: 市場
  - name: Reuters Japan - Top
    url: https://assets.wor.jp/rss/rdf/reuters/top.rdf
    category: 総合
  - name: Reuters Japan - Business
    url: https://assets.wor.jp/rss/rdf/reuters/business.rdf
    category: ビジネス
  - name: Investing.com Japan - News
    url: https://jp.investing.com/rss/news.rss
    category: マーケット
```

**v1.1 以降の有料オプション** (コード対応のみ。設定は空でも動く):
- 日経電子版 RSS (ユーザー契約が必要)
- X (Twitter) API v2 (有料、$100/月)
- 各証券会社スクレイピング (SBI証券マーケットレポート等)

**取得処理**:
- 過去24時間以内の記事に限定
- 重複除去: URL hash + タイトル Levenshtein距離
- 記事全文取得 (RSS summary だけでなく requests でページ本文も)
- 文字化け対策: chardet で自動判定

### B. 要約・フィルタ (summarize.py)

取得した記事を Gemini Flash (or Claude Haiku) に投げて:

1. **関連度スコアリング** (0-10点)
   - config.yaml の `holdings` (保有銘柄) と `interests` (興味分野) に照らして採点
   - 7点以上 = 必読 / 5-6点 = その他注目 / 4点以下 = 除外

2. **モード別フォーマット化**

#### ハイブリッドモード (デフォルト)
```
📰 Zundamon投資ニュース [2026-05-08 06:30]

🔥 必読 (あなたの保有: NVDA)
【NVDA】AI需要強く、第2Qガイダンス上方修正 +8.3%
→ 💡 初心者向け: 会社が「もっと儲かる」と発表したので、
  保有株は上昇する可能性が高いのだ
→ 📎 https://...

📊 その他注目
【S&P500】過去最高値更新
  └ 💡 S&P500 = 米国主要500社の平均指数
```

#### 初心者モード (beginner)
```
📰 Zundamon投資ニュース [2026-05-08 06:30]

🔥 必読 (保有: NVDA)

【何が起きた?】
  エヌビディアが決算発表で、次の3ヶ月の業績予想を
  上方修正したのだ
  
【どういう意味?】
  会社が「これまで以上に儲かりそう」と自信を示した
  ので、株価が上がる可能性が高いのだ
  
【あなたへの影響】
  保有中の NVDA は明日の市場開始で上昇する可能性大
  短期売却は焦らず、長期なら買い増し候補なのだ
  
【専門用語解説】
  「ガイダンス」= 会社が発表する将来の業績予想
```

#### 上級者モード (expert)
```
📰 Zundamon投資ニュース [2026-05-08 06:30]

🔥 必読 (保有: NVDA)
【NVDA】AI需要強く、第2Qガイダンス上方修正 +8.3%
 → 要約: 第2QのRevenue予測 +8.3%、AIインフラ投資継続
 → 元記事: https://...

📊 その他注目
【S&P500】過去最高値更新、利下げ観測で...
```

**Mode selection**: `config.yaml` の `mode` フィールドで指定。ツール実行時に動的に選択可。

### C. 配信 (deliver.py)

Discord Webhook への POST。Rich Embed 形式を活用して見やすく整形。

**配信タイミング**:
- デフォルト: 毎日 06:30 JST (GitHub Actions cron: `30 21 * * *` UTC換算)
- ユーザー設定可: `config.yaml` の `delivery_time_jst` で変更

**失敗時の処理**:
- Webhook 送信失敗 → GitHub Actions のログに記録 + 次回再試行
- API レート制限 → リトライ with exponential backoff
- 取得記事ゼロ → 「今日は注目記事なしなのだ」メッセージ送信

### D. GitHub Actions cron

`.github/workflows/daily.yml`:
```yaml
name: Daily News Digest
on:
  schedule:
    - cron: '30 21 * * *'  # 06:30 JST
  workflow_dispatch:  # 手動実行ボタン

jobs:
  digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/run.py
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
```

---

## 📁 プロジェクト構造

```
ZundaNewsConcierge/
├── README.md                           # 概要・使い方ハイレベル (視聴者向け)
├── SETUP_GUIDE.md                      # ゲーミフィケーション型セットアップ手順
├── TROUBLESHOOTING.md                  # よくある詰まり方
├── LICENSE                             # MIT
├── requirements.txt                    # Python 依存関係
├── config.yaml.example                 # ユーザーが編集するテンプレ
├── sources.yaml                        # RSS ソース定義
├── .github/
│   └── workflows/
│       └── daily.yml                   # GitHub Actions cron
├── scripts/
│   ├── run.py                          # エントリポイント
│   ├── fetch.py                        # RSS 取得・重複除去
│   ├── summarize.py                    # AI で要約・スコアリング
│   └── deliver.py                      # Discord 配信
├── prompts/
│   ├── relevance_check.md              # 関連度判定プロンプト
│   ├── digest_beginner.md              # 初心者モード要約
│   ├── digest_expert.md                # 上級者モード要約
│   └── digest_hybrid.md                # ハイブリッド (デフォルト)
├── examples/
│   └── sample_config.yaml              # 主の実保有銘柄ベースのサンプル
├── tests/
│   └── test_fetch.py                   # 最小テスト
└── docs/
    ├── architecture.md                 # アーキテクチャ説明
    └── prompts_design.md               # プロンプト設計の意図
```

---

## 📄 config.yaml の構造

ユーザーが編集する唯一のファイル。なるべく日本語コメントで説明。

```yaml
# ============================================
# Zundamon 投資ニュースコンシェルジュ 設定
# ============================================

# モード: beginner / expert / hybrid (デフォルト推奨)
mode: hybrid

# 配信時刻 (JST, 24時間表記)
delivery_time_jst: "06:30"

# 使用するAI ("gemini" or "claude")
ai_provider: gemini

# --------------------------------------------
# 保有銘柄 (ティッカーと銘柄名をセットで書いて)
# --------------------------------------------
holdings:
  - ticker: NVDA
    name: エヌビディア
  - ticker: AAPL
    name: アップル
  - ticker: MSFT
    name: マイクロソフト
  # ... あなたの保有銘柄を追加

# --------------------------------------------
# 興味分野 (キーワードで指定)
# --------------------------------------------
interests:
  - S&P500
  - 新NISA
  - 半導体
  - AI
  - 円安
  - 金利
  # ... 興味のある分野を追加

# --------------------------------------------
# 避けたいトピック (ニュースから除外)
# --------------------------------------------
exclude:
  - 仮想通貨
  - IPO

# --------------------------------------------
# 配信記事数の上限
# --------------------------------------------
limits:
  top_count: 3         # 必読セクションの記事数
  notable_count: 7     # その他注目セクションの記事数
```

### 主の実保有銘柄サンプル

`examples/sample_config.yaml` には主の `tousimeigara_itirann.png` からの抽出を入れる。

**タスク**: 実装時にDOUGA_JIDOUKA/assets/screenshots/tousimeigara_itirann.png を開いて保有銘柄を抽出し、サンプル config に反映。

---

## 🎮 ゲーミフィケーション SETUP_GUIDE 仕様

SETUP_GUIDE.md を**クエスト形式**で書く。以下の原則で：

1. 各ステップにチェックボックス `- [ ]` を付ける
2. LEVEL 1〜4 で進行、各LEVELクリア時に🎖Badge
3. 最終到達時に👑称号「朝の30分を奪還した者」
4. 全ステップに**スクリーンショット**を付ける (実装者が用意)
5. 躓きポイントには💡ヒント
6. 完走所要時間を明示 (目安30-40分)

### 構造案

```markdown
## 🏆 セットアップ・クエスト

### ⚙️ LEVEL 1: 準備の章 (所要10分)
- [ ] **Quest 1-1** Google アカウントにサインイン
  - スクショ: login_google.png
- [ ] **Quest 1-2** Gemini API キーを取得
  - スクショ: gemini_apikey_step1.png (aistudio.google.com)
  - スクショ: gemini_apikey_step2.png (Get API key ボタン)
  - スクショ: gemini_apikey_step3.png (キーをコピー)
- [ ] **Quest 1-3** Discord アカウント作成
  - ...
🎖 Badge: 「準備マスター」 を獲得!

### 🔧 LEVEL 2: 配置の章 (所要10分)
...

### 🎨 LEVEL 3: カスタマイズの章 (所要5分)
...

### 🚀 LEVEL 4: 起動の章 (所要5分)
...

🏆 全クエスト完了! あなたは 👑「朝の30分を奪還した者」 の称号を獲得しました!
```

### 効果
- チェックボックス埋めたい心理 → 完走率アップ
- Badge / 称号 → スクショシェアがバズ素材
- **#ずんだ投資秘書** ハッシュタグで視聴者参加型コンテンツ化

---

## 💰 コスト試算 (ユーザー側・月額)

### 完全無料パターン (Gemini Flash + GitHub Actions + Discord)
| 項目 | コスト |
|---|---|
| GitHub Actions | ¥0 (公開repo 2000分/月 無料枠) |
| Gemini Flash API | ¥0 (1日100万トークン無料枠内に収まる) |
| Discord Webhook | ¥0 |
| **合計** | **¥0/月** |

### 高品質パターン (Claude Haiku)
| 項目 | コスト |
|---|---|
| Anthropic Claude Haiku API | ¥300-500/月 (毎日利用想定) |
| GitHub Actions | ¥0 |
| Discord | ¥0 |
| **合計** | **¥300-500/月** |

---

## 🛠 実装タスク (新セッション用チェックリスト)

### Phase 1 - 基盤実装 (1日)
- [ ] `requirements.txt` 作成 (feedparser, google-generativeai, anthropic, requests, pyyaml)
- [ ] `sources.yaml` に Bloomberg / Reuters / Investing.com の無料RSS URL列挙
- [ ] `config.yaml.example` 作成 (この SPEC の構造に従う)
- [ ] `scripts/fetch.py` 実装 (RSS 取得 + 過去24h フィルタ + 重複除去)
- [ ] `scripts/summarize.py` 実装 (Gemini/Claude 切替 + モード別プロンプト)
- [ ] `scripts/deliver.py` 実装 (Discord Webhook Rich Embed送信)
- [ ] `scripts/run.py` メインエントリ作成
- [ ] `prompts/` 配下のプロンプトテキスト 4種作成

### Phase 2 - GitHub Actions (0.5日)
- [ ] `.github/workflows/daily.yml` 作成
- [ ] Secrets 設定テスト
- [ ] 手動 workflow_dispatch 動作確認

### Phase 3 - 主用設定 & 本番テスト (0.5日)
- [ ] DOUGA_JIDOUKA の `tousimeigara_itirann.png` から保有銘柄抽出
- [ ] 主の `examples/sample_config.yaml` 作成
- [ ] 主の Discord サーバーで初回配信テスト
- [ ] 1週間運用テスト

### Phase 4 - ドキュメント & ゲーミフィケーション (1日)
- [ ] `README.md` 作成 (ハイレベルな概要)
- [ ] `SETUP_GUIDE.md` 作成 (クエスト形式・スクショ用プレースホルダ)
- [ ] 実際のセットアップ動画を録画してスクショ抽出
- [ ] `TROUBLESHOOTING.md` 作成 (よくある詰まり方)
- [ ] `docs/architecture.md`, `docs/prompts_design.md` 作成

### Phase 5 - 公開準備 (0.5日)
- [ ] リポジトリを GitHub に公開 (public)
- [ ] Template Repository として設定
- [ ] LICENSE (MIT) 追加
- [ ] EP19 動画撮影用のデモ環境整備

---

## 🎬 EP19 動画連携

### タイトル案 (CTR重視)
1. 【無料配布】毎朝30分の情報収集をAIに任せて0分にした方法
2. 【Zundamon 投資秘書】Claudeで作った AIニュース秘書を無料公開なのだ
3. 【年間180時間節約】朝のニュース巡回をAIに奪還させる方法

### 配信日
2026-05-08 (金) 06:30 AM 予約公開想定

### 動画構成 (約15分)
- greeting (22s): 源泉徴収票 + 30代1200万3000万
- problem_intro (18s): 毎朝30分の情報収集は年180時間消費
- demo (90s): 主のDiscordに今朝届いた実際のダイジェスト
- inside (60s): RSS→AI→Discord 3段構造
- sources (45s): Bloomberg/Reuters/Investing.com
- mode_toggle (60s): 🆕 初心者/上級者ハイブリッド切替のデモ
- setup_quest (90s): 🎮 クエスト形式のセットアップ紹介
- cost_reality (45s): Gemini無料枠で月0円運用可能
- distribution (60s): GitHub Fork手順
- advanced (30s): ゲーマー・副業・節税に拡張できる話
- summary (30s): 朝の30分を奪還しよう

---

## 🔮 将来拡張ロードマップ

| Version | 配布 | 対応時期 |
|---|---|---|
| v1.0 | 投資ニュース版 (EP19) | 5/8 金 |
| v1.1 | 有料ソース対応 (日経/X API) | 6月 |
| v1.2 | 副業案件監視版 | 6月末 |
| v1.3 | 節税・税制改正版 | 7月 |
| v2.0 | **ゲーム情報コンシェルジュ** | 8月 |
| v2.1 | ゲーム自動化ツール連携 | 9月 |
| v3.0 | Web UI (Vercel hosted) | 秋 |

---

## 📝 運用ルール (新セッションで実装者が守ること)

1. **非エンジニアファースト**: いかなるドキュメントも Python 知らない人が読める日本語で
2. **YAML > Python**: ユーザーが触るのは YAML だけ。Python は隠蔽
3. **スクショ優先**: エラーが起きる可能性のある箇所には必ずスクショ
4. **プロンプトを外部ファイル化**: `prompts/` 配下、後で調整しやすく
5. **テスト**: 最低 `fetch.py` の RSS パース部分はユニットテスト書く

---

## 🔗 参考リソース

### 既存OSS (参考のみ・フォークしない)
- [Horizon - AI News Radar](https://github.com/Thysrael/Horizon)
- [auto-news](https://github.com/finaldie/auto-news)
- [n8n Daily Briefing Template](https://n8n.io/workflows/13527-summarize-ai-news-from-rss-reddit-and-hn-with-claude-to-discord-and-slack/)

### 技術資料
- [feedparser ドキュメント](https://feedparser.readthedocs.io/)
- [Google Generative AI Python SDK](https://ai.google.dev/tutorials/python_quickstart)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Discord Webhook docs](https://discord.com/developers/docs/resources/webhook)

### 関連プロジェクト (sibling)
- `C:\Users\koufu\Documents\DOUGA_JIDOUKA\` ← 動画自動化 (別プロジェクト、触らない)
- `C:\Users\koufu\Documents\DOUGA_SATELLITE\` ← 動画サテライト (別プロジェクト)

---

## 🚨 実装者への注意

1. **このプロジェクトは `DOUGA_JIDOUKA` から完全に独立**。相互のimport や 依存関係は作らない
2. **Python パッケージは ZundaNewsConcierge 内の venv に隔離** (DOUGA_JIDOUKA と混ざらないように)
3. **API キーは絶対にコミットしない**。`.gitignore` に `*.key`, `.env`, `secrets.yaml` を追加
4. **デフォルトの `ai_provider: gemini`** 固定 (視聴者が無料で使えることが最優先)
5. **主のPCでは Claude Haiku API に切替可能な構造**にする (運営と視聴者で同じコードベース)

---

## ✅ 新セッション開始時に Claude へ渡すメッセージのテンプレ

```
このプロジェクトの目的は SPEC.md を読んで。
DOUGA_JIDOUKA プロジェクトとは独立した新規プロジェクトで、
ZundaNewsConcierge という投資ニュース自動配信ツールを作る。

Phase 1 から順に実装してほしい。
まず requirements.txt と sources.yaml を作って、
次に fetch.py を書いて、RSS 取得が動くか確認してほしい。

日本語で会話して、「〜なのだ」口調は不要。
```

---

*最終更新: 2026-04-24*
*スペック作成者: Claude (DOUGA_JIDOUKA セッション)*
*実装者: 新規 Claude Code セッション (このリポジトリ内で起動)*

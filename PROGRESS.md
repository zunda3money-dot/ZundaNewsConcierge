# 🚀 Zundamon News Concierge 実装進捗

**最終更新**: 2026-04-29 (🛡 **本番初実トラブル対応: Gemini 503 エラーへの自動リトライ実装**)

## 🌐 公開リポジトリ

**https://github.com/zunda3money-dot/ZundaNewsConcierge** (Public Template)

- Test Setup workflow 本番環境 ✅ Success 確認済み
- Discord 経由のセットアップが GitHub Actions ランナー上で動作確認

---

## 📊 全体進捗

```
Claude が実施可能な作業のみで集計:
[████████████████████] 100%  (17 / 17 タスク)
```

🎉 **Claude 実行可能分は全て完了しました**

残るは 🖐 手元作業のみです (GitHub へ push / Secrets 登録 / 実配信テスト / スクショ撮影)。

---

## 🗂 フェーズ別

### ✅ Phase 1: 基盤実装
```
[████████████████████] 100%  (8/8)
```
- [x] `requirements.txt`
- [x] `sources.yaml` (5 フィード)
- [x] `config.yaml.example`
- [x] `scripts/fetch.py`
- [x] `scripts/summarize.py`
- [x] `scripts/deliver.py`
- [x] `scripts/run.py`
- [x] `prompts/` 4 ファイル (relevance + digest 3 モード)

### ✅ Phase 2: GitHub Actions
```
[████████████████████] 100%  (Claude 分 1/1)
```
- [x] `.github/workflows/daily.yml`
- [x] **Discord Webhook URL 取得 + ローカル接続テスト送信成功** ✅ (2026-04-27)
- [x] **Gemini API キー取得** ✅ (2026-04-27)
- [x] **🎉 E2E フルパイプライン Discord 実配信成功** ✅ (2026-04-27)
  - RSS 取得 22 件 → 重複除去 21 件 → AI スコア → ダイジェスト → Discord 配信、合計 約 50 秒
  - Gemini SDK を旧 `google-generativeai` から後継 `google-genai` (gemini-2.5-flash) に移行
- [ ] 🖐 GitHub Secrets (`GEMINI_API_KEY`, `DISCORD_WEBHOOK_URL`) 登録 — **手元作業** (push 後)
- [ ] 🖐 `workflow_dispatch` で初回手動実行テスト — **手元作業**

### ✅ Phase 3: 主用設定
```
[████████████████████] 100%  (Claude 分 2/2)
```
- [x] `tousimeigara_itirann.png` から保有抽出 (FANG+ 構成10銘柄 + インデックス系interests)
- [x] `examples/sample_config.yaml`
- [ ] 🖐 主の Discord サーバーで初回配信テスト — **手元作業**
- [ ] 🖐 1週間運用テスト — **手元作業**

### ✅ Phase 4: ドキュメント & ゲーミフィケーション
```
[████████████████████] 100%  (Claude 分 5/5)
```
- [x] `README.md` 視聴者向け本版に書き換え (Badge, 配信サンプル, FAQ 含む)
- [x] `SETUP_GUIDE.md` クエスト形式 (4 LEVEL / 所要30-40分 / Badge + 称号)
- [x] `TROUBLESHOOTING.md` (よくある9項目の逆引き)
- [x] `docs/architecture.md` (3 段パイプライン詳解 + 設計判断の記録)
- [x] `docs/prompts_design.md` (プロンプト設計意図 + 改変ガイド)
- [ ] 🖐 実セットアップ動画録画 → スクショ抽出 → `docs/screenshots/` に配置 — **手元作業**

### ✅ Phase 5: 公開準備
```
[████████████████████] 100%  (Claude 分 1/1)
```
- [x] `LICENSE` (MIT)
- [ ] 🖐 GitHub に push & Public 公開 — **手元作業**
- [ ] 🖐 Template Repository 設定 — **手元作業**
- [ ] 🖐 EP19 デモ環境整備 — **手元作業**

---

## ✨ 後追いで実装した新機能 (2026-04-27)

### ① 1 日 2 回配信 (朝 06:00 + 夕 19:00 JST)
- `.github/workflows/daily.yml` の cron を 2 行に
- 全プロンプトに `{{SESSION_LABEL}}` `{{SESSION_CONTEXT}}` 変数を追加
- `summarize.py::_session_label()` が JST 時刻から「朝のレポート/夕方のレポート」を自動判定
- 朝は米国市場クローズ動向、夕方は日本市場総括 + 米国プレビューに自動フォーカス

### ② ポートフォリオ画像 → config.yaml 自動生成
- 新ファイル: `scripts/config_from_image.py` + `prompts/config_from_image.md`
- Gemini 2.5 Flash の multimodal 機能で画像を解析
- 投資信託/ETFを構成銘柄に自動分解、interests も自動提案
- 主のスクショで実機テスト: 12 銘柄 + 15 interests を 20 秒で生成 (手作業より精度高い)
- **配布想定の修正** (ユーザー指摘): 視聴者は **AI Studio のブラウザチャット**に画像と
  プロンプトを貼る形でブラウザ完結。`scripts/config_from_image.py` は主本人 / Codespaces
  ユーザー / 開発者向けに格下げして位置付けを明確化
- プライバシー注意 (口座残高マスク必須、無料 Gemini は学習に使われる可能性) を SETUP_GUIDE と
  README FAQ に明記

### ③ Gemini SDK 移行
- 旧 `google-generativeai` (deprecated) → 後継 `google-genai`
- デフォルトモデル `gemini-1.5-flash` (404) → `gemini-2.5-flash` (現行)
- viewers がフォーク時に詰むのを予防

### ⑧ 本番初トラブル対応 — Gemini 503 自動リトライ (2026-04-29)
- **発生**: 4/28 19:00 JST 予定の cron が GitHub Actions の混雑で **6 時間遅延**、4/29 1:28 JST に実行 → そのタイミングで Gemini API も高負荷で **503 UNAVAILABLE** を返した
- **エラーハンドラは正常動作**: Discord に「⚠️ Zundamon News Concierge エラー」が届いて主が気づけた
- **対策実装**: `AIClient` に外側リトライ層を追加
  - 503/502/504 (ServerError) と 429 (RateLimit) を一時的エラーとして判定
  - 60s → 180s → 300s の指数バックオフで最大 3 回試行
  - 認証失敗等の非一時的エラーは即座に上げて無駄リトライ防止
  - Gemini と Claude 両方の SDK エラー型に対応
- **手動リトライで成功配信確認** (4/29 のテスト)
- TROUBLESHOOTING に 503 ケースのユーザー向けガイドを追加

### ⑦ 5 人格ユーザーテストによる QUICK_START 改良 (2026-04-28)
- **Web 調査**: GitHub Actions / Use this template / Gmail App Password / Discord Webhook の各カテゴリで非エンジニアの躓きパターンを調査
- **5 人格を組成して walkthrough**:
  - ①田中真理子 (45歳・専業主婦) → Step 3 で 80% 離脱予測
  - ②佐藤健一 (32歳・営業) → 完走可能性 70%
  - ③山本悦子 (58歳・公務員) → 95% 離脱予測
  - ④鈴木美咲 (27歳・IT総務) → 完走 95%、SNS 拡散候補
  - ⑤鈴木和夫 (62歳・退職者) → 99% 離脱、家族支援必須層
- **改良点 9 件を反映**:
  - 完成プレビューを冒頭に追加
  - AI Studio 英語画面に Chrome 翻訳手順を明記
  - API キー画面 / Secrets 画面への直リンク導線
  - Use this template と Code 緑ボタンの混同防止注記
  - Secret Name は手打ち禁止 (コピペ必須) を強調
  - Gmail 2段階認証必須を Gmail ルート冒頭に
  - アプリパスワード「スペース許容」を強調
  - 赤い × 時のサマリー読み方を明記
  - 用意するもの欄に各☑の用途を併記
- 結果: ④鈴木美咲レベルなら 7 分完走、③山本悦子レベルでも家族支援なしで完走見込み

### ⑥ 差別化機能 — 「他のニュースアプリにない」2 機能
**EP19 で打ち出す目玉**:

#### 🎯 買い増しシグナル (主案)
- ユーザーが冷静なときに `config.yaml` に書いた `buy_signals` ルール (例: NVDA target_below: 110) を毎回チェック
- 終値がラインを下回った日にダイジェスト冒頭に **🎯 ルール発動** ブロックを挿入
- 価格データ: yfinance (Yahoo Finance、無料、API キー不要)。日本株は `.T` 付き ticker 対応
- 規制リスク回避のため**「投資助言ではなく事前設定ルールが満たされた通知」**という表現で統一
- yfinance 取得失敗時は graceful degradation (本体配信は止めない)

#### 🔄 反対論点の自動併記 (確証バイアス対策)
- 3 モード全 digest プロンプトに「反対論点 (🔄)」ブロック追加
- 必読セクションの全記事に弱気/慎重派の見方を 1 行で必ず併記
- 既存の投資ニュースアプリには一切ない差別化要素
- 例: 「→ 🔄 反対論点: PER 38x は 5年高位、Q4 ガイダンスにキャパ供給制約リスク」

### ⑤ QUICK_START 7分プラン (奥様向け簡易導線)
- 新ファイル: `QUICK_START.md` (Discord 主推奨、3 ステップ構成)
- 新ファイル: `scripts/test_setup.py` + `.github/workflows/test_setup.yml`
  → workflow_dispatch 1 クリックで全 Secret を 10 秒で診断
- `summarize.py` に **デフォルトプロファイル fallback** (holdings/interests 両方空でも一般市場ニュースが届く)
- `run.py` に **EMAIL_TO 環境変数オーバーライド** (config.yaml 編集なしで Secret だけで完結)
- 結果: **奥様の手元作業が ~7 分**(Discord) / ~10 分(Gmail) に圧縮

### ④ Gmail (SMTP) 配信対応 — multi-channel dispatch
- 新ファイル: `scripts/deliver_email.py` (Gmail SMTP_SSL 経由、HTML + plain text の multipart)
- `scripts/run.py` を multi-channel に refactor (新関数 `channels_enabled` / `deliver_all`)
- 環境変数 + config の状態で**自動的に有効化**:
  - `DISCORD_WEBHOOK_URL` だけ → Discord のみ
  - `GMAIL_FROM` + `GMAIL_APP_PASSWORD` + `config.email_to` だけ → Gmail のみ
  - 全部揃えれば → 両方に届く
- 一部チャネルが失敗しても他のチャネルは試行 (耐障害性)
- `.github/workflows/daily.yml` に `GMAIL_FROM` / `GMAIL_APP_PASSWORD` env 追加
- SETUP_GUIDE に「🅰 Discord ルート / 🅱 Gmail ルート」の二択 + 両方併用可能な構成
- TROUBLESHOOTING に Gmail 認証失敗 / 迷惑メールフォルダ等のセクション追加
- **奥さんへの配布想定** (Discord 不要、Gmail で完結) に対応

---

## 🔧 現在の作業

**Claude 側の作業はゼロ。主本人の手元作業待ち。**

主がやるべきこと (優先順):

1. **GitHub に push** (ルート A/B/C から選択。詳細は以前のやり取り参照)
2. **Secrets 登録** (`GEMINI_API_KEY`, `DISCORD_WEBHOOK_URL`)
3. **Template Repository 設定** (Settings → Template repository チェックボックス)
4. **セットアップ動画の録画** → スクショを `docs/screenshots/` に配置
5. **EP19 動画撮影用デモ準備**

---

## 📁 生成物サマリー

```
ZundaNewsConcierge/
├── .github/workflows/daily.yml           ← cron (06:30 JST)
├── .gitignore
├── LICENSE                                (MIT)
├── PROGRESS.md                            (このファイル)
├── README.md                              (視聴者向け)
├── SETUP_GUIDE.md                         (🎮 クエスト形式)
├── SPEC.md                                (完全スペック、既存)
├── TROUBLESHOOTING.md                     (逆引き 9 項目)
├── config.yaml.example                    (ユーザー編集テンプレ)
├── requirements.txt                       (Python 依存)
├── sources.yaml                           (RSS 5 feeds)
├── docs/
│   ├── architecture.md                    (3 段パイプライン)
│   └── prompts_design.md                  (プロンプト設計)
├── examples/
│   └── sample_config.yaml                 (主の実保有ベース)
├── prompts/
│   ├── relevance_check.md                 (スコアリング)
│   ├── digest_hybrid.md                   (デフォルト)
│   ├── digest_beginner.md                 (初心者モード)
│   └── digest_expert.md                   (上級者モード)
├── scripts/
│   ├── __init__.py
│   ├── fetch.py                           (RSS 取得+重複除去)
│   ├── summarize.py                       (AI スコア+生成)
│   ├── deliver.py                         (Discord Webhook)
│   └── run.py                             (エントリポイント)
└── tests/
    ├── __init__.py
    └── test_fetch.py                      (9 テスト合格)
```

**合計**: 20 ファイル、2,500 行超 (Python ~700 行 + プロンプト ~200 行 + ドキュメント ~1,600 行)

---

## 📌 凡例

| マーク | 意味 |
|---|---|
| ✅ | Phase 完了 (Claude 分) |
| 🟡 | 進行中 |
| ⏳ | 未着手 |
| 🖐 | **手元作業** (主本人の作業) |

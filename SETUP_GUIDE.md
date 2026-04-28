# 🏆 セットアップ・クエスト - 朝の30分を奪還せよ

> ⏱️ **所要時間の目安**: 30〜40分
> 💰 **コスト**: 0円 (Gemini 無料枠利用時)
> 💻 **必要スキル**: コピペができる、Google 検索ができる、Discord が使える。**Python 知識は一切不要**

このガイドを最後まで完走すると、**朝 6:00 + 夕 19:00 の 1 日 2 回、あなた専用の投資ニュースダイジェストが Discord に届く**ようになります。
朝は米国市場のクローズ動向、夕方は日本市場の総括 + 米国市場プレビュー — 時間帯に応じて AI が自動で観点を切り替えます。

---

## 🎮 ルール

- 各 LEVEL は **10 分以内**で終わるように作られています
- 各 Quest にはチェックボックス `- [ ]` があります。GitHub 上でこのファイルを開くとタップでチェックできます
- 🎖 LEVEL クリアごとに Badge が手に入ります (スクショをツイートすると #ずんだ投資秘書 のバズ素材になります)
- 最終到達時、あなたは 👑 称号 **「朝の30分を奪還した者」** を獲得します

## 🗺 クエスト一覧

| LEVEL | 章 | 所要時間 |
|---|---|---|
| 1 | 準備の章 | 10分 |
| 2 | 配置の章 | 10分 |
| 3 | カスタマイズの章 | 5分 |
| 4 | 起動の章 | 5分 |

---

## ⚙️ LEVEL 1: 準備の章 (所要10分)

この章では、3 つの外部サービスのアカウントと API キー/Webhook URL を用意します。

### 🔹 Quest 1-1: Google アカウントでサインイン

> **何のため?**: 無料の AI「Gemini」を使うためです

- [ ] **Step 1**: ブラウザで [https://aistudio.google.com/](https://aistudio.google.com/) を開く
  - 📸 スクショ: `docs/screenshots/quest_1_1_aistudio_top.png`
- [ ] **Step 2**: 右上の「Sign in」から普段使っている Google アカウントでログイン
  - 💡 **ヒント**: 広告が大量に飛んでくるのが嫌なら、投資情報専用に新しい Google アカウントを作るのがおすすめ

### 🔹 Quest 1-2: Gemini API キーを取得 (最重要)

> **何のため?**: このキーが「AI に記事を要約させる権利」になります

- [ ] **Step 1**: Google AI Studio 左上の「Get API key」ボタンをクリック
  - 📸 スクショ: `docs/screenshots/quest_1_2_step1_get_api_key.png`
- [ ] **Step 2**: 「Create API key」→「Create API key in new project」をクリック
  - 📸 スクショ: `docs/screenshots/quest_1_2_step2_create.png`
- [ ] **Step 3**: 表示された `AIzaSy...` で始まる文字列をコピー
  - 📸 スクショ: `docs/screenshots/quest_1_2_step3_copy.png`
  - ⚠️ **注意**: このキーは**他人に絶対に見せない**。Twitter に貼った日には誰かに勝手に使われます
  - 💡 **ヒント**: メモ帳に一旦貼っておく。LEVEL 2 でまた使います

### 🔹 Quest 1-3: 配信先を選ぶ (Discord または Gmail)

> **何のため?**: 毎朝のニュースが届く「場所」を決めます

**お好みで以下から選んでください**。両方設定すれば両方に届きます。

| 選択肢 | おすすめな人 | 所要時間 |
|---|---|---|
| 🅰 **Discord** | チャットアプリで気軽に読みたい人 | 3 分 |
| 🅱 **Gmail (メール)** | 普段からメールでニュースを読み慣れている人、Discord は使ってない人 | 5 分 |

---

#### 🅰 Discord ルート (Quest 1-3a → 1-4a)

##### Quest 1-3a: Discord アカウントと通知用サーバーを用意

- [ ] **Step 1**: [https://discord.com/](https://discord.com/) にアクセスしてアカウント作成 (既にあればスキップ)
- [ ] **Step 2**: Discord アプリを開き、左サイドバーの「＋」→「オリジナルの作成」→「自分と友達のため」を選択
  - 💡 **ヒント**: サーバー名は「投資ニュース」「朝のダッシュボード」など好きなものでOK。自分しか入らない一人用サーバーで問題なし
  - 📸 スクショ: `docs/screenshots/quest_1_3a_create_server.png`

##### Quest 1-4a: Discord チャンネルの Webhook URL を取得

- [ ] **Step 1**: 通知を受けるチャンネル (例: `#general`) の **歯車アイコン** をクリック
  - 📸 スクショ: `docs/screenshots/quest_1_4a_step1_gear.png`
- [ ] **Step 2**: 左メニューから「連携サービス」→「ウェブフック」→「新しいウェブフック」
  - 📸 スクショ: `docs/screenshots/quest_1_4a_step2_webhook.png`
- [ ] **Step 3**: 作成されたウェブフックの「ウェブフックURLをコピー」ボタンを押す
  - 📸 スクショ: `docs/screenshots/quest_1_4a_step3_copy_url.png`
  - ⚠️ **注意**: `https://discord.com/api/webhooks/...` で始まる URL です。これも他人に見せない
  - 💡 **ヒント**: アイコンと名前を「ずんだもん投資秘書」にすると通知が気分良くなります

---

#### 🅱 Gmail ルート (Quest 1-3b → 1-4b)

##### Quest 1-3b: Gmail の 2 段階認証を有効化

> **何のため?**: アプリパスワード (Gmail から SMTP 送信するための専用キー) は 2 段階認証必須です

- [ ] **Step 1**: ブラウザで [https://myaccount.google.com/security](https://myaccount.google.com/security) を開く
- [ ] **Step 2**: 「Google へのログイン」セクションで **「2 段階認証プロセス」が ON** になっているか確認
  - すでに ON なら次のクエストへ
  - OFF の場合は「2 段階認証プロセス」をクリックして手順に従って ON にする (電話番号を登録するだけ、3 分)
  - 📸 スクショ: `docs/screenshots/quest_1_3b_2fa.png`

##### Quest 1-4b: Gmail アプリパスワードを発行

> **何のため?**: 通常のログインパスワードではなく、このアプリ専用の 16 桁パスワードを使います

- [ ] **Step 1**: ブラウザで [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) を開く
  - 💡 もし「アプリパスワード」のページが見当たらない場合は、Quest 1-3b の 2 段階認証が有効か再確認
- [ ] **Step 2**: 「アプリ名」欄に `Zundamon News` と入力 → 「作成」
  - 📸 スクショ: `docs/screenshots/quest_1_4b_create_app_password.png`
- [ ] **Step 3**: 表示された 16 桁の英数字 (例: `abcd efgh ijkl mnop`) を**メモ帳にコピー**
  - ⚠️ **注意**: このページを閉じると再表示されません。**必ずコピーしてから閉じる**
  - ⚠️ **注意**: スペースが入っていますが、コピペで OK (空白は自動除去されます)
  - 📸 スクショ: `docs/screenshots/quest_1_4b_copy_password.png`
- [ ] **Step 4**: 自分の Gmail アドレス (例: `your-name@gmail.com`) と、配信先メールアドレス (自分宛で OK、家族宛でも可) もメモ
  - 💡 **配信先と送信元は同じでも違っていても OK**。「自分の Gmail から自分宛に届く」が一番シンプル

---

### 🎖 LEVEL 1 CLEAR: Badge 「準備マスター」 獲得!

> 3 つの材料 (Google, Gemini API Key, Discord Webhook URL) が揃いました。次は配置です。

---

## 🔧 LEVEL 2: 配置の章 (所要10分)

この章では、このリポジトリを**あなたのもの**にして、Secrets に先ほどのキー類を登録します。

### 🔹 Quest 2-1: Template からリポジトリを複製

> **何のため?**: あなた専用のコピーを作ります

- [ ] **Step 1**: このリポジトリの右上「**Use this template**」 → 「Create a new repository」
  - 📸 スクショ: `docs/screenshots/quest_2_1_step1_use_template.png`
- [ ] **Step 2**: Repository name を `my-news-concierge` など好きな名前に (半角英数字 + ハイフン推奨)
- [ ] **Step 3**: **Private** を選択 (Public だと自分の保有銘柄が世界中に見えます ⚠️)
  - 📸 スクショ: `docs/screenshots/quest_2_1_step3_private.png`
- [ ] **Step 4**: 「Create repository」

### 🔹 Quest 2-2: GitHub Secrets に必要なキーを登録

> **何のため?**: API キーを安全に保管する GitHub の金庫です

- [ ] **Step 1**: 自分のリポジトリの **Settings** タブ → 左メニュー **Secrets and variables** → **Actions**
  - 📸 スクショ: `docs/screenshots/quest_2_2_step1_secrets_menu.png`
- [ ] **Step 2**: 「New repository secret」ボタンを押して、選んだルートに応じて以下を登録:

#### 共通 (必須)

| Name (完全一致) | Value |
|---|---|
| `GEMINI_API_KEY` | Quest 1-2 でコピーした `AIzaSy...` |

#### 🅰 Discord ルートを選んだ人

| Name (完全一致) | Value |
|---|---|
| `DISCORD_WEBHOOK_URL` | Quest 1-4a でコピーした `https://discord.com/api/webhooks/...` |

#### 🅱 Gmail ルートを選んだ人

| Name (完全一致) | Value |
|---|---|
| `GMAIL_FROM` | 送信元 Gmail アドレス (例: `your-name@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Quest 1-4b でコピーした 16 桁の英数字 (空白入りでも OK) |

#### 両方選んだ人

両方の表の Secret を登録 (Discord と Gmail の両方に届くようになります)

  - 📸 スクショ: `docs/screenshots/quest_2_2_step3_add_secret.png`
  - 💡 **ヒント**: Secret は登録後は値が見えなくなります。安心です
  - ⚠️ **注意**: Name のスペル間違い (例: `GEMINI_API_key` とか) は NG。**完全一致**が必要

### 🔹 Quest 2-3: Actions を有効化

> **何のため?**: このリポジトリで自動実行を許可します

- [ ] **Step 1**: リポジトリの **Actions** タブを開く
  - Template からコピーした直後は "Workflows aren't being run" の警告が出ていることがあります
- [ ] **Step 2**: 緑色の「I understand my workflows, go ahead and enable them」ボタンを押す
  - 📸 スクショ: `docs/screenshots/quest_2_3_enable_actions.png`

---

### 🎖 LEVEL 2 CLEAR: Badge 「配置の番人」 獲得!

> もう半分終わりました。残るはあなた好みへのカスタマイズです。

---

## 🎨 LEVEL 3: カスタマイズの章 (所要5分)

自分の投資スタイルに合わせて設定ファイルを編集します。ブラウザ上の編集だけで完結します。

### 🎁 Quest 3-1 (★お手軽ルート): 保有スクショから AI Studio に config を作らせる

> **何のため?**: 自分で YAML を書くのが面倒な人向け、ブラウザだけで完結 **5 分**。
> ⚡ 投資信託・ETF・金/銀/原油等のコモディティ・個別株 すべて対応。Gemini が画像から読み取って、構成銘柄レベルまで分解した config を作ります。

#### 🛡 事前準備: スクショから個人情報を消す (重要)

無料の Gemini はあなたの画像が**Google の AI 学習に利用される可能性**があります ([プライバシーポリシー](https://policies.google.com/privacy))。
そのためアップロード前に以下をマスクしてください:

- [ ] **Step 0**: スクショを撮ったら、Windows なら**「ペイント」「切り取り＆スケッチ」**で以下を黒塗り:
  - 口座残高 / 評価金額の具体的な数字
  - 取得金額 / 損益の具体的な金額
  - 口座 ID / 氏名 / メアドが映っている部分

  💡 銘柄名・銘柄数・ファンド名は**残してOK** (これがないと AI が分析できません)

#### 配信用 config を作る

- [ ] **Step 1**: ブラウザで [Google AI Studio](https://aistudio.google.com/) を開く (Quest 1-2 で使った場所)
- [ ] **Step 2**: 左サイドバーの「Create Prompt」または「Chat」を選択
- [ ] **Step 3**: 入力欄左下の **クリップ📎マーク** で**マスクしたスクショ**をアップロード
- [ ] **Step 4**: 以下のプロンプトをコピーして貼り付け、送信:

  <details>
  <summary>📋 プロンプト全文 (クリックで展開してコピー)</summary>

  ```
  あなたはポートフォリオ画像を解析して config.yaml を生成する AI です。

  以下のルールで、画像から読み取れる保有銘柄・ファンドを config.yaml に変換してください。

  - 投資信託・ETFは構成銘柄に分解 (例: FANG+ → NVDA, META, AAPL...)
  - 個別株はティッカーをそのまま使う
  - 金/銀/原油等のコモディティは関連キーワードを interests に
  - 保有から推測される interests を 8〜15 個自動提案
  - 出力は YAML のみ、前後に説明文不要

  出力フォーマット:
  ```yaml
  mode: hybrid
  delivery_time_jst: "06:00, 19:00"
  ai_provider: gemini

  holdings:
    - ticker: <識別子>
      name: <日本語名>

  interests:
    - <キーワード>

  exclude:
    - 仮想通貨
    - IPO

  limits:
    top_count: 3
    notable_count: 7

  advanced:
    score_threshold_top: 7
    score_threshold_notable: 5
    lookback_hours: 24
  ```
  ```

  </details>

- [ ] **Step 5**: AI が出力した YAML 全文をコピー
- [ ] **Step 6**: 自分の GitHub リポジトリに移動 → 「Add file」→「Create new file」
  - ファイル名: `config.yaml`
  - 内容: コピーした YAML を貼り付け
- [ ] **Step 7**: ページ下「Commit changes」→「Commit directly to the main branch」→ 緑ボタン

#### 注意

- ⚠️ Step 0 で個人情報マスクを忘れると、Google の AI 学習に**残高情報まで使われる**可能性があります
- ⚠️ どうしてもマスクが面倒な人は **「手動ルート」(下) を選んでください**
- ⚠️ Claude / ChatGPT の課金アカウントを持っているなら、そちらに同じプロンプトを貼ると学習されません ([Claude のプライバシー](https://www.anthropic.com/privacy) / [ChatGPT のプライバシー](https://openai.com/policies/privacy-policy))

---

### 🔹 Quest 3-1 (手動ルート): config.yaml を手書きする

> **何のため?**: あなたの保有銘柄と興味を AI に教えます (画像をどこにもアップしたくない人、細かくコントロールしたい人向け)

- [ ] **Step 1**: リポジトリトップで `config.yaml.example` ファイルを開く
- [ ] **Step 2**: 右上の「📋 Copy raw file」ボタンで全内容をコピー
  - 📸 スクショ: `docs/screenshots/quest_3_1_step2_copy_raw.png`
- [ ] **Step 3**: リポジトリトップに戻り、「Add file」→「Create new file」
  - ファイル名欄に `config.yaml` と入力 (拡張子に注意)
- [ ] **Step 4**: コピーした内容を貼り付け
- [ ] **Step 5**: 以下を**自分向けに書き換え**:

  - `holdings`: 自分の保有銘柄 (ティッカーと日本語銘柄名)
  - `interests`: 気になるキーワード (例: `新NISA`, `円安`, `AI` 等)
  - `exclude`: 避けたいトピック (例: `仮想通貨`, `IPO`)
  - `mode`: `hybrid` (おすすめ) / `beginner` (用語解説付き) / `expert` (数字だけ)
  - **🅱 Gmail ルートの人のみ** `email_to`: 配信先メールアドレス (例: `"your-name@gmail.com"`)。
    Discord ルートのみの人は空欄 `""` のままで OK
  - **(任意・推奨) `buy_signals`**: 「冷静なときに決めた押し目買いライン」をここに書いておくと、
    そのラインに株価が到達した日にダイジェスト冒頭で通知されます (詳細はファイル内コメント参照)

  💡 **ヒント**: 何を書けばいいか分からない場合は `examples/sample_config.yaml` (主のサンプル) を参考にしてください

- [ ] **Step 6**: 下にスクロールして「Commit changes」→「Commit directly to the main branch」→ 緑ボタン
  - 📸 スクショ: `docs/screenshots/quest_3_1_step6_commit.png`

---

### 🎖 LEVEL 3 CLEAR: Badge 「調律師」 獲得!

> あと一息。動作確認だけです。

---

## 🚀 LEVEL 4: 起動の章 (所要5分)

最後に、**明日の朝まで待たずに**今すぐ動くかテストします。

### 🔹 Quest 4-1: 手動で 1 回走らせてみる

- [ ] **Step 1**: リポジトリの **Actions** タブを開く
- [ ] **Step 2**: 左サイドバーの **"Daily News Digest"** ワークフローをクリック
- [ ] **Step 3**: 右側の **"Run workflow"** ドロップダウン → **"Run workflow"** ボタン (緑)
  - 📸 スクショ: `docs/screenshots/quest_4_1_step3_run.png`
- [ ] **Step 4**: 20〜30 秒ほどで新しい行が増えます。その行をクリックすると進捗が見えます
  - 💡 **ヒント**: 「digest」ジョブがオレンジ → 緑チェックになれば成功
  - ⚠️ **失敗 (赤 ×)** した場合は [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) を参照してください

### 🔹 Quest 4-2: Discord に届いているか確認

- [ ] **Step 1**: Discord で通知チャンネルを開く
- [ ] **Step 2**: 「📰 Zundamon投資ニュース」 で始まるメッセージが届いていれば成功
  - 📸 スクショ: `docs/screenshots/quest_4_2_discord_received.png`
  - 💡 **ヒント**: 「今日は注目記事なし」と返ってきても正常。RSS に新着がなかっただけ

### 🔹 Quest 4-3: (任意) 配信時刻を変える

初期設定は **朝 06:00 JST + 夕 19:00 JST の 1 日 2 回**。変えたい場合:

- [ ] `.github/workflows/daily.yml` を編集
- [ ] `cron: '0 21 * * *'` (= 朝 06:00 JST) と `cron: '0 10 * * *'` (= 夕 19:00 JST) の行を編集
  - 例: 朝のみで夕方は不要 → 夕方の cron 行を削除
  - 例: 07:00 JST に変更したい → `0 22 * * *`
  - 💡 **ヒント**: [crontab.guru](https://crontab.guru/) で UTC 時刻を確認できます (JST = UTC + 9 時間)

---

### 🎖 LEVEL 4 CLEAR: Badge 「自動化の達成者」 獲得!

---

## 🏆 全クエスト完了!

```
あなたは
👑「朝の30分を奪還した者」
の称号を獲得しました
```

これで明日から毎朝 6:30 に、AI が厳選したあなた向けの投資ニュースが Discord に届きます。年間換算で **180 時間 (約 7.5 日分)** の情報収集時間を節約する計算です。

### 🐦 シェア推奨

達成スクショを `#ずんだ投資秘書` で投稿してください。主の RT 対象です。

### 🔧 設定をアップデートしたくなったら

- 保有銘柄が増えた → `config.yaml` を GitHub UI で編集
- モードを変えたい → `config.yaml` の `mode` を書き換え
- 時刻を変えたい → `.github/workflows/daily.yml` の cron を書き換え

### ❓ 困ったら

[TROUBLESHOOTING.md](./TROUBLESHOOTING.md) に「よくある詰まり方」を全部まとめています。

---

**Happy Investing!**

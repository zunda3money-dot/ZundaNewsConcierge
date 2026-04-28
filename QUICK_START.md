# ⚡ 7分セットアップ - とりあえず動かす

> **目標**: パソコンが苦手な人でも **7 分以内** に「明日の朝、Discord に投資ニュースが届く」状態にする。
>
> 📨 メールで欲しい人は本ページの末尾「**Gmail で受け取りたい人へ**」を参照。+2〜4 分かかります。

---

## 🛒 用意するもの

- [ ] Google アカウント (普段使いの Gmail で OK)
- [ ] GitHub アカウント (なければ [github.com](https://github.com/) で 1 分)
- [ ] Discord アカウント (なければ [discord.com](https://discord.com/) で 1 分、PC でもスマホでも可)

Python・コマンドライン・課金プラン**一切不要**。完全無料で動きます。

---

## ⏱ 3 ステップ (合計 7 分)

### 🔹 Step 1 - Gemini の API キーを取る (3 分)

> **これは何?**: 「AI に記事を要約してもらう権利」。完全無料。

1. [https://aistudio.google.com/](https://aistudio.google.com/) を開く → Google でログイン
2. 左上 **「Get API key」** → **「Create API key」** → **「Create API key in new project」**
3. `AIzaSy...` で始まる文字列が出る → **メモ帳にコピー** (⚠️ 他人に見せない)

✅ **完了サイン**: メモ帳に `AIzaSy...` が貼ってある

---

### 🔹 Step 2 - Discord Webhook を作る (1 分)

> **これは何?**: 「ニュースの配達先住所」。Discord の通知チャンネルが受け口になります。

1. Discord を開いて、通知を受けたいサーバーを選ぶ
   - 💡 まだサーバーが無い場合: 左サイドバーの「＋」→「オリジナルの作成」→「自分と友達のため」で **30 秒で作成**
2. 通知を受けるチャンネル (例: `#general`) の **歯車アイコン ⚙️** をクリック
3. 左メニュー **「連携サービス」** → **「ウェブフック」** → **「新しいウェブフック」**
4. 作成された Webhook の **「ウェブフック URL をコピー」** ボタン
5. URL (`https://discord.com/api/webhooks/...`) を**メモ帳にコピー** (⚠️ 他人に見せない)

✅ **完了サイン**: メモ帳に `https://discord.com/api/webhooks/...` が貼ってある

---

### 🔹 Step 3 - リポジトリを複製して 2 つ Secret を入れて Test 実行 (3 分)

> **これは何?**: 自分専用のコピーを GitHub に作って、キーを安全に保管→ 動作確認まで一気にやります。

#### 3-1. Template から自分のリポジトリを作る (30 秒)

1. このリポジトリの右上 **「Use this template」** → 「Create a new repository」
2. Repository name: 何でも OK (例: `my-news-concierge`)
3. **必ず「Private」にチェック** (他人に見られないように)
4. 「Create repository」

#### 3-2. Secret を 2 つ登録する (1 分)

5. 自分のリポジトリで **Settings** タブ → 左メニュー **Secrets and variables** → **Actions**
6. **「New repository secret」**ボタンを押して、**以下 2 つ**を 1 つずつ登録:

| Name (完全一致) | Value |
|---|---|
| `GEMINI_API_KEY` | Step 1 でコピーした `AIzaSy...` |
| `DISCORD_WEBHOOK_URL` | Step 2 でコピーした `https://discord.com/api/webhooks/...` |

⚠️ **大事**: Name のスペル大文字・アンダースコア完全一致でコピペ。

#### 3-3. Actions を有効化する (10 秒)

7. **Actions** タブを開く → 緑色の「**I understand my workflows, go ahead and enable them**」を押す

#### 3-4. テスト実行 (1 分)

8. **Actions** タブ → 左サイドバー **「Test Setup (セットアップ確認)」** → 右側 **「Run workflow」** → 緑の **「Run workflow」**ボタン
9. 30 秒待って、新しい行が **緑のチェック ✅** になれば成功
   - 赤い ❌ の場合は、その行をクリックしてログを開く → どの Secret が間違っているか具体的に教えてくれます

10. **Discord を開いて確認**: 「✅ セットアップ確認: Discord Webhook OK です」 のメッセージが届いていれば**完成**!

✅ **完了サイン**: Discord に確認メッセージが届いた

---

## 🏆 完成!

明日の朝 **06:00**、夕方 **19:00** に、AI が厳選したダイジェストが自動配信されます。

```
📰 Zundamon投資ニュース (朝のレポート) [2026-04-28 06:00 JST]

🔥 必読
【NVDA】AI需要強く決算上方修正 +8.3%
→ 💡 ...

📊 その他注目
...
```

---

## 🤔 「自分の保有銘柄に合わせたい」と思ったら

最初は **「S&P500」「新NISA」「米国株」「半導体」** など一般的な投資家向けキーワードで動いています。これでも十分実用的ですが、自分仕様にしたい場合:

→ [SETUP_GUIDE.md](./SETUP_GUIDE.md) の **Quest 3-1** で保有銘柄を AI に教えられます。**ポートフォリオ画像 → AI が自動 config 作成**のお手軽ルートあり。

**急がなくて大丈夫**。まず数日使って「もっとこういう記事ほしい」と思ったら触りに来てください。

---

## 📨 Gmail で受け取りたい人へ (+2〜4 分)

Discord ではなくメール派の人は、Step 2 を以下に差し替え:

<details>
<summary>📥 Gmail 受信のセットアップ (クリックで展開)</summary>

### Step 2-Gmail: 2 段階認証 → アプリパスワード発行

1. [https://myaccount.google.com/security](https://myaccount.google.com/security) で **「2 段階認証プロセス」が ON** か確認
   - OFF なら有効化 (電話番号登録だけ、3 分)
2. [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) を開く
3. アプリ名に `Zundamon News` と入れて **「作成」**
4. 16 桁の英数字をメモ帳にコピー (⚠️ 閉じると 2 度と見られない)

### Step 3-Gmail: Secret を **4 つ**登録

| Name | Value |
|---|---|
| `GEMINI_API_KEY` | Step 1 の `AIzaSy...` |
| `GMAIL_FROM` | あなたの Gmail (例: `your-name@gmail.com`) |
| `GMAIL_APP_PASSWORD` | 上記 16 桁 |
| `EMAIL_TO` | 受信先メアド (自分宛なら GMAIL_FROM と同じ) |

### Step 3-Gmail で Test Setup を実行

Gmail 受信トレイに「✅ Zundamon News - セットアップ確認 OK」 が届けば完成。
迷惑メールフォルダも念のため確認してください。

</details>

**Discord と Gmail を併用したい人**: 両方の Secret を登録すれば**両方に届きます**。

---

## ❓ 困ったら

- **Step 3 で赤い ❌ → ログを見る** ([TROUBLESHOOTING.md](./TROUBLESHOOTING.md) のセクション 1)
- **Discord に届かない** → [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) セクション 2
- **メールが届かない** → [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) セクション 3

---

## 📜 設計の意図

このプランは **「まず動く実感を得る」** ことを最優先しました。
保有銘柄の細かい設定は後回しでも、デフォルトで実用的な一般市場ダイジェストが届きます。
慣れてからカスタマイズすれば良いのです。

# 🛠 トラブルシューティング

「セットアップは終えたのに動かない!」「何かエラーが出た!」というときの逆引き集です。

上から順に、**よくある順** に並んでいます。

---

## 🆘 セクション 0 (最強): AI にスクショを見せて聞く

このページの本文を読む前に、**まずこれを試してください**。
**このツールを作っている本人 (非エンジニア) もこのやり方で日々の問題を解決しています。**

### 手順 (30 秒)

1. エラーが出ている画面 / 詰まっている画面のスクショを撮る
   - Windows: `Win` + `Shift` + `S`
   - Mac: `Cmd` + `Shift` + `4`
   - スマホ: 通常のスクリーンショット
2. [Gemini](https://gemini.google.com/) / [ChatGPT](https://chat.openai.com/) / [Claude](https://claude.ai/) のいずれかを開く
3. 以下プロンプトをコピペ + スクショ添付して送信

<details>
<summary>📋 トラブル相談プロンプト (クリックで展開してコピー)</summary>

```
私は非エンジニアで、GitHub にある「Zundamon News Concierge」
(https://github.com/zunda3money-dot/ZundaNewsConcierge) という
無料の投資ニュース配信ツールを使っています。

添付のスクショで赤い × やエラーメッセージが出ています。
何が原因で、私が次に何をすればよいか、
専門用語を避けて、小学生にもわかる日本語で教えてください。

私の状況:
- 何をしようとしていたか: ?? (← 自分で記入)
- どのステップで起きたか: Step ?-? (← 自分で記入)
- 既に試したこと: ?? (← 自分で記入)
```

</details>

> 💡 **画像読み取りは Gemini が一番得意**: Google アカウントだけで使えるので、Step 1 で取った API キーと同じ Google アカウントでそのまま [gemini.google.com](https://gemini.google.com/) にログインしてください。

下記の本文セクション (1〜10) も併せて参考にどうぞ。

---

## 🔎 目次

1. [GitHub Actions が赤い × で失敗している](#1-github-actions-が赤い--で失敗している)
2. [Discord に通知が来ない](#2-discord-に通知が来ない)
3. [Gmail にメールが届かない](#3-gmail-にメールが届かない)
4. [「今日は注目記事なし」と毎日言われる](#4-今日は注目記事なしと毎日言われる)
5. [配信時刻がズレる](#5-配信時刻がズレる)
6. [Gemini の無料枠を使い切った](#6-gemini-の無料枠を使い切った)
7. [config.yaml を編集したのに反映されない](#7-configyaml-を編集したのに反映されない)
8. [記事の要約が変な日本語になる](#8-記事の要約が変な日本語になる)
9. [Actions が勝手に無効化される](#9-actions-が勝手に無効化される)
10. [エラーメッセージの検索](#10-エラーメッセージの検索)

---

## 1. GitHub Actions が赤い × で失敗している

**症状**: Actions タブで実行履歴を開くと赤い × マーク、ログに `Error:` が出ている。

### 原因別チェックリスト

#### 🔴 `GEMINI_API_KEY が設定されていません`

Secrets の登録漏れまたはタイプミスです。

- [ ] リポジトリの **Settings → Secrets and variables → Actions** を開く
- [ ] `GEMINI_API_KEY` が存在するか確認
- [ ] 名前が **完全一致** しているか (小文字の `gemini_api_key` や末尾スペースはNG)
- [ ] Claude を使う設定の場合は `ANTHROPIC_API_KEY` も必要

#### 🔴 `DISCORD_WEBHOOK_URL が未設定です`

- [ ] 同じく Secrets に `DISCORD_WEBHOOK_URL` を登録
- [ ] URL 全体 (`https://discord.com/api/webhooks/...` で始まる) をコピペ。`https://` を抜かない

#### 🔴 `400 Client Error: Bad Request for url: https://discord.com/...`

Webhook URL が失効したか、削除されたチャンネル/サーバーを指しています。

- [ ] Discord で該当 Webhook を作り直す → 新しい URL を Secrets に **更新** (削除 + 再作成)

#### 🔴 `429 Too Many Requests` が連発する

Discord 側のレート制限。通常は 1 日 1 回配信なので起きにくいですが、`workflow_dispatch` を連打したときに起きます。

- [ ] 15 分ほど置いてから再実行

#### 🔴 `ModuleNotFoundError: No module named 'feedparser'`

依存関係のインストールに失敗。Actions のネットワーク障害の可能性。

- [ ] **Actions タブ → 同じワークフロー → Re-run jobs** で再実行
- [ ] それでも直らない場合は `requirements.txt` を変更していないか確認

---

## 2. Discord に通知が来ない

**Actions は緑 ✅ なのに Discord に届かない場合**、Webhook が間違ったチャンネルを指しています。

- [ ] Discord で「連携サービス → ウェブフック」を開き、**「通知を受けたいチャンネル」と Webhook の対象チャンネルが一致** しているか確認
- [ ] 違うサーバーの別チャンネルに飛んでいる場合は削除 → 正しいチャンネルで作り直す

**Actions が赤い ×** の場合は、[セクション 1](#1-github-actions-が赤い--で失敗している) を先に解決してください。

---

## 3. Gmail にメールが届かない

### 🔴 `Gmail 認証失敗 (535, b'5.7.8 Username and Password not accepted')`

**最頻出**。原因はほぼ「アプリパスワードではなく通常のログインパスワードを Secrets に登録している」です。

- [ ] [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) で 16 桁のアプリパスワードを発行
- [ ] **2 段階認証** が ON になっているか確認 ([Google アカウント セキュリティ](https://myaccount.google.com/security))
  - OFF だと「アプリパスワード」メニュー自体が出てきません
- [ ] GitHub Secrets の `GMAIL_APP_PASSWORD` の値を発行した 16 桁に置き換え (古い値は削除)
- [ ] スペースは付けたままでも除去しても OK (コード側で吸収します)

### 🔴 `Gmail 送信失敗: [Errno 11001] getaddrinfo failed` 等のネットワーク系

GitHub Actions ランナーから一時的に SMTP に到達できない問題。

- [ ] 数分後にもう一度 `workflow_dispatch` で手動実行
- [ ] それでも継続する場合は GitHub の障害情報を確認

### 🔴 メールが「迷惑メール」フォルダに入る

初回送信時に Gmail が「身元不明」と判定することがあります。

- [ ] 迷惑メールフォルダを開く → 該当メールを開く → 「迷惑メールではない」をクリック
- [ ] 以降は受信トレイに直接届きます

### 🔴 GitHub Actions は緑 ✅ で「Email 配信完了」のログがあるのに届かない

- [ ] config.yaml の `email_to` が**自分の正しいメールアドレス**になっているか確認
- [ ] 送信元 (`GMAIL_FROM` Secret) のメールアドレス自身に**自分から自分へ**は届くか確認
- [ ] 受信側のメーラーで**送信元アドレスをフィルタしていないか**確認

---

## 4. 「今日は注目記事なし」と毎日言われる

AI による関連度判定で、**あなたの保有銘柄・興味キーワードに合う記事が閾値未満**だと発生します。

### 対処

- [ ] `config.yaml` の `holdings` に、**実際にニュースが出る銘柄**が入っているか確認
  - 例: 投資信託 (例: オルカン) そのものは RSS に出ないので、構成銘柄 (NVDA 等) で書く
- [ ] `interests` のキーワードを広げる
  - 例: `新NISA`, `円安`, `金利`, `米国株`, `日銀` など
- [ ] 閾値を下げる: `config.yaml` の `advanced.score_threshold_top` を 7 → 6 に、`score_threshold_notable` を 5 → 4 に
- [ ] `sources.yaml` に好きなフィードを追加

### 参考にする

[`examples/sample_config.yaml`](./examples/sample_config.yaml) に、主本人のインデックス投資ベース設定例があります。

---

## 5. 配信時刻がズレる

### GitHub Actions の cron は**最大 15 分程度の遅延**がある仕様です。

- GitHub 公式の仕様として、cron の起動が遅れることがあります (特に毎時 00 分付近は世界中の job が集中して遅れやすい)
- 06:30 JST 指定でも 06:35〜06:45 ごろに届くことがある、と覚えておいてください

### 別の時刻に変えたい

- [ ] `.github/workflows/daily.yml` の `cron: '30 21 * * *'` を編集
  - フォーマット: `分 時 日 月 曜日` (UTC 時刻)
  - JST は UTC + 9 時間。例: 07:00 JST = 22:00 UTC → `cron: '0 22 * * *'`
  - 💡 [crontab.guru](https://crontab.guru/) で検算できます

---

## 6. Gemini の無料枠を使い切った

**エラー例**: `429 RESOURCE_EXHAUSTED` / `quota exceeded` / `Quota exceeded for metric: ...generate_content_free_tier_requests, limit: 20`

Gemini Flash の無料枠には**いくつかの制限**があります:
- **1 日 20 リクエスト** (gemini-2.5-flash 無料枠、2026年現在)
- 1 分 15 リクエスト
- 1 日 100 万トークン

通常の運用 (1 日 2 回配信 × 3〜4 calls) では 8 calls/日程度で済むので余裕ですが、**Test Setup を 1 日に何度も叩く** / **手動 workflow_dispatch を連打** すると到達します。

### 対処

- [ ] **24 時間待つ** (無料枠は毎日 UTC 00:00 にリセット、JST 09:00)
- [ ] 1 日のテスト回数を絞る (Setup 確認は 1〜2 回で十分)
- [ ] **Claude Haiku に切替** (Anthropic 課金、月 300-500 円、無料枠制限なし)
  - `config.yaml` の `ai_provider: claude` + Secrets に `ANTHROPIC_API_KEY` を追加
- [ ] 記事取得数を減らす: `config.yaml` の `limits.top_count` / `limits.notable_count` を小さくする (使用トークン削減)

⚠️ Quota は **ユーザーごと**に独立しているので、視聴者個人の利用には影響しません。主が EP19 デモ準備でテストを連打するときに気をつけてください。

---

## 7. config.yaml を編集したのに反映されない

### 原因

- [ ] **ブランチに push し忘れ** → 編集後「Commit changes」 → 「Commit directly to the main branch」を押したか確認
- [ ] **YAML のインデント崩れ** → インデントは**スペース 2 個 or 4 個で統一**。タブ文字はNG
- [ ] **config.yaml ではなく config.yaml.example を編集していた** → 反映されるのは `config.yaml` の方

### YAML の書き方ミス検出

- [ ] Actions タブのログに `yaml.scanner.ScannerError` が出ていたら構文ミス
- [ ] [YAML Validator](https://www.yamllint.com/) にコピペして構文チェック

---

## 8. 記事の要約が変な日本語になる

### Gemini Flash は Claude より文章の丁寧さで劣る傾向があります。

### 対処

- [ ] `config.yaml` の `ai_provider: claude` に変更 (月 300-500 円、ANTHROPIC_API_KEY が別途必要)
- [ ] プロンプトを自分で調整: `prompts/digest_hybrid.md` などを編集して「より丁寧な敬語で」などの指示を足す
  - 編集後は commit を忘れずに

---

## 9. Actions が勝手に無効化される

### GitHub の仕様で、**60 日以上リポジトリに push がない場合**、cron ワークフローは自動停止します。

### 対処

- [ ] Actions タブ → `Daily News Digest` → 右上「Enable workflow」で再有効化
- [ ] 予防策: たまに `config.yaml` を微編集して push する (60 日カウンタがリセットされます)

---

## 10. エラーメッセージの検索

ここに載っていないエラーが出た場合:

1. **Actions のログ** (赤 × 行をクリック → 詳細展開) から `Error:` 行をコピー
2. **GitHub Issues** で既存の報告があるかチェック: [Issues ページ](../../issues)
3. なければ **New Issue** を立てて:
   - エラーメッセージ全文
   - `config.yaml` の中身 (API キー部分を伏せる)
   - いつから起きているか

報告には `#ずんだ投資秘書` をつけると主本人が気づきやすいです。

---

## 🆘 どうしても分からないとき

最終手段として、主本人の Discord サーバーに「困ったチャンネル」があります (チャンネル詳細は [ずんだもんの三刀流マネーラボ](https://youtube.com/@...) の概要欄参照)。

ただし、**APIキーや Webhook URL は絶対に貼らないでください**。誰でも見えます。エラーメッセージだけを貼ってください。

# lp-agent-kit：AIエージェントが LP（ランディングページ）を作って公開するキット

あなたの AIエージェント（Claude Code など）にこのフォルダを読ませると、次の仕事を手順どおりに進めます。

1. **聞き取り** … 売りたいもの・お客様・強み・申し込みの先（LINE・フォーム）を質問して埋める
2. **訴求の型を選ぶ** … PASONA・QUEST などから、商品に合う流れを選ぶ
3. **LP の文章** … 型に沿って見出し・本文・ボタンの言葉を書く
4. **HTML 1ファイル** … スマホ優先・軽い（見本で約10KB）。デザインの型は3つ（simple／bold／soft）
5. **無料の置き場に公開** … GitHub Pages または Cloudflare Pages
6. **LINE 登録ボタン・フォーム・計測** … LINE の友だち追加リンク、Google フォームなど、UTM 付きリンク、GA4（任意）

## 費用

- このキット自体に月額費用はありません。こちらのサーバーや鍵は一切使いません。
- かかるのは **あなたが使う AIエージェントの利用料** だけです。
- 置き場は無料の枠で始められます（GitHub Pages は公開リポジトリなら無料。Cloudflare Pages は無料プランあり）。独自ドメインを使うならドメイン代がかかります。

## 最初の10分

用意するもの：Python 3.11 以上、AIエージェント。

```bash
# 1. 見本の LP を3つの型で作ってみる（1分）
python3 scripts/build_lp.py examples/lp-content.json --design simple --out dist/simple.html
python3 scripts/build_lp.py examples/lp-content.json --design bold   --out dist/bold.html
python3 scripts/build_lp.py examples/lp-content.json --design soft   --out dist/index.html

# 2. ブラウザで開いて見比べる（2分）
open dist/index.html        # Windows は start dist\index.html

# 3. 機械チェック（1分）
python3 scripts/check_lp.py dist/index.html
```

気に入った型が決まったら、AIエージェントに次のように頼みます。

> 「AGENT.md を読んで、わたしのオンライン講座の LP を作って。聞き取りから始めて」

エージェントが `templates/hearing-sheet.md` の質問をし、`content/<名前>.json` を書き、HTML を作り、公開手順まで進めます。

## 必要なキー・アカウント

| 用途 | 必要なもの | 必須か |
|---|---|---|
| 公開（どちらか） | GitHub アカウント／Cloudflare アカウント | どちらか1つ |
| LINE 登録ボタン | LINE 公式アカウント（友だち追加の URL） | 使うときだけ |
| フォーム | Google フォームなど、送信を受け取れるフォームのサービス | 使うときだけ |
| 計測 | GA4 の測定 ID（`G-` で始まる） | 任意 |
| Cloudflare を道具で公開 | Node.js と、`npx wrangler login` または API トークン | Cloudflare を使うときだけ |

- **LINE の友だち追加 URL**：LINE Official Account Manager の［ホーム］→［友だちを増やす］→［友だち追加ガイド］で URL・QR・ボタンが作れます。URL の形は `https://line.me/R/ti/p/%40あなたのID`（`@` は `%40`）です。
- **GA4 の測定 ID**：Google アナリティクスで「プロパティ」→「データストリーム（ウェブ）」を作ると表示されます。
- **Cloudflare の API トークン**（任意）：Cloudflare のダッシュボード →「My Profile」→「API Tokens」で作れます。使わない場合は `npx wrangler login` を一度だけ人が打ってブラウザで許可します。

## 中身

| 置き場 | 中身 |
|---|---|
| `AGENT.md` | AIエージェントへの指示書 |
| `CLAUDE.md` | Claude Code に AGENT.md を読ませる1行 |
| `playbooks/` | 作業ごとの手順（01 聞き取り 〜 09 法律） |
| `templates/` | 聞き取りシート・訴求の型・デザイン3つ（CSS）・特商法とプライバシーポリシーの雛形 |
| `scripts/` | 補助の道具（公開する道具は `--go` を付けたときだけ動く） |
| `examples/lp-content.json` | 架空の見本の中身 |
| `content/` | あなたの LP の中身（JSON）を置く場所 |
| `dist/` | できた HTML（Git に入れない） |

### scripts の一覧

| 道具 | すること | ネット |
|---|---|---|
| `build_lp.py` | 中身の JSON とデザインから HTML 1枚を作る | 使わない |
| `check_lp.py` | 重さ・スマホ設定・ボタン・法律の入口などを機械で確かめる | 使わない |
| `utm_link.py` | 媒体ごとの UTM 付きリンクを作る | 使わない |
| `deploy_cloudflare.py` | Cloudflare Pages へ公開（Wrangler を呼ぶ） | `--go` のときだけ |
| `publish_github_pages.py` | 公開用リポジトリへ写して push | `--go` のときだけ |

## できないこと（正直に）

- **フォームの送信を受け取る仕組みは入っていません。** 静的な HTML だけではフォームの中身を保存できないため、Google フォームなど外のフォームへのリンク、または埋め込みにします。
- **GitHub Pages を無料で使えるのは公開（public）リポジトリだけです。** 非公開のリポジトリから公開するには GitHub の有料プランが要ります。このキットのリポジトリそのものではなく、LP だけを置く公開用リポジトリを別に作ってください。
- **Cloudflare Pages を道具で公開するには Node.js が要ります。** Node.js を入れない場合は、Cloudflare の画面で `dist` フォルダをドラッグ&ドロップして公開できます（手順は playbooks/07-publish.md）。
- **画像は作りません。** 写真・図はあなたが用意し、`dist/` に置いて JSON で指定します（重さに注意）。
- **LINE の公式ボタン画像は同梱していません。** LINE の公式素材を使うときは LINE の案内と規約に従ってください。このキットのボタンは文字だけの緑のボタンです。
- **売れることを約束するものではありません。** 法律の確認を代わりにするものでもありません（playbooks/09-law.md）。


---

## このキットは N-Hack のAIエージェント専用です

このキットは N-Hack の受講生さん専用のプレゼントです。**N-Hack のAIエージェント
（N-Hack のプラグインを入れた Claude Code など）が、このパソコンで動いていること**を
前提にしています。

- どのスクリプトも、最初に `scripts/nhack_gate.py`（門）を通ります。門は、このパソコンに
  N-Hack のAIエージェントの「印」があるかを**読むだけ**で確かめます（ネットにつなぎません・
  何も書き換えません・プラグインには一切触れません）。
- 印が足りない環境では、スクリプトは動かずに止まります（終了コード 2）。この環境でだけ
  動くのが正しい姿です。
- いま N-Hack 環境かどうかは、次のコマンドで確かめられます。

```bash
python3 scripts/nhack_gate.py
```

N-Hack 以外のパソコンにコピーしても動きません。受講生ページ・コンサルチャンネルの案内に
沿ってご利用ください。


---

## 困ったとき・もっと伸ばしたいとき

分からない・動かない・時間がかかっている——そんなときは、ひとりで抱えないでください。
**N-Hack の受講生ページ／個別コンサルチャンネル**から、担当にそのまま相談できます。
あなた専用のAIと伴走しながら、最短で結果まで一緒に持っていきます。

このキットのAIは、あなたが詰まったときや区切りのときに、自分から相談先を案内します。

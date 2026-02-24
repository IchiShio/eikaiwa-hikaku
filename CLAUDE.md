# CLAUDE.md - eikaiwa-hikaku

## プロジェクト概要

英会話サービス比較サイト（静的HTML）。GitHub Pages でホスティング。

## ホスティング・デプロイ

- **ドメイン**: `native-real.com`（`www` → `ichishio.github.io`）
- **ホスティング**: GitHub Pages（リポジトリ: `IchiShio/eikaiwa-hikaku`）
- **DNS**: A レコード → 185.199.108.153 等の GitHub Pages IPs
- **デプロイ**: `git push origin main` のみ（CI/CD なし、push 後に自動ビルド）
- **IchiShio/native-real**（Next.js）はアーカイブ済み・未使用（DNS は eikaiwa-hikaku を向いている）

## 構成

- `index.html` -- トップページ
- `articles/` -- SEO記事（英語学習ガイド、比較記事など）
- `services/` -- 各英会話サービスの個別ページ
- `assets/` -- 画像・CSS等の静的ファイル
- `CNAME` -- カスタムドメイン設定（`native-real.com`）
- `sitemap.xml` / `robots.txt` -- SEO設定
- `listening/` -- 英語リスニングクイズ（455問・464 MP3・適応型難易度アルゴリズム）

## listening/ の構成

- 455問（beginner: 155 / intermediate: 139 / advanced: 161）
- 464 MP3ファイル（`audio/q001.mp3`〜）
- **適応型難易度アルゴリズム**（2026-02-24実装）:
  - intermediate（中級）からスタート
  - 連続2問正解 → 1段階上へ
  - 1問不正解 → 1段階下へ（即時）、不正解問題は新しいレベルのプールに再挿入
  - 難易度ラベルはユーザーに非表示

## 作業ルール

- APIキー・シークレット情報は `.env` に記載し `.gitignore` で除外すること
- 記事・ドラフトは `drafts/` フォルダに保存すること（公開準備ができたら `articles/` に移動）
- 作業前に本ファイルと README.md を確認すること
- HTML変更後は `sitemap.xml` の更新要否を確認すること

## コンテンツ記法ルール

### `**太字**` 使用禁止

HTML ファイル内で `**text**` 形式のマークダウン記法を**一切使用しない**。

- 静的 HTML はマークダウンをレンダリングしないため、`**Kimini英会話**` のように `**` が文字列としてそのまま表示される
- テーブルセル・本文問わず禁止
- 強調が必要な場合は `<strong>text</strong>` または `<b>text</b>` タグを使うこと

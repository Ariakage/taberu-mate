<h1 align="center">TaberuMate<br/><a href="../LICENSE">
    <img src="https://img.shields.io/badge/license-AGPL--3.0--only-blue.svg?style=flat-square" alt="License: AGPL-3.0-only" />
  </a><a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.13+" />
  </a><a href="https://nodejs.org/">
    <img src="https://img.shields.io/badge/node.js-24%2B-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js 24+" />
  </a><a href="https://vuejs.org/">
    <img src="https://img.shields.io/badge/vue-3-42b883?style=flat-square&logo=vuedotjs&logoColor=white" alt="Vue 3" />
  </a><a href="https://docs.astral.sh/uv/">
    <img src="https://img.shields.io/badge/package%20manager-uv-261230?style=flat-square" alt="uv" />
  </a></h1>

<p align="center">
  <a href="../README.md">简体中文</a> | <a href="README.en.md">English</a> | 日本語
</p>

<p align="center">
  <a href="https://github.com/ariakage/taberu-mate">
    <img src="assets/header.png" alt="TaberuMate Logo" />
  </a>
  <br />
  <strong>食べ友——知らないメニューも怖くない、旅先のおいしいごはんに寄り添う相棒ですにゃ〜</strong>
</p>

## ✨ 特長

- **📷 写真一枚でメニューを認識**

  スマホでレストランのメニューを撮るだけで、AI が自動で認識し、手入力なしで操作できるデジタルメニューを生成します

- **🍽️ QR オーダー / デリバリーアプリ風の注文体験**

  料理の写真、価格、説明をなじみのある注文画面で確認でき、多言語切り替えにも対応しています

- **🌍 現地語へのスマート翻訳**

  エージェントがメニューを母語、または旅行先で使いたい言語へ一括翻訳します。100 以上の言語に対応し、自然な翻訳を目指します

- **🌟 スマート絞り込みと忌避・アレルギーメモ**

  味、価格、辛さ、ベジタリアン対応などで絞り込み可能。注文メモのように苦手な食材や避けたい条件も入力できます

- **🔏 プライバシーと安全性**

  自分専用の軽量プラットフォームとしてすばやく複製・運用でき、ワークフローを手元で管理できます

## 🚀 クイックスタート

### Step1 リポジトリをクローン
```bash
git clone https://github.com/Ariakage/taberu-mate.git
```

### Step2-1 Python 環境を準備
```bash
cd taberu-mate/backend
uv sync # パッケージマネージャーとして uv を事前にインストールしてください
```

### Step2-2 Vue 環境を準備
```bash
cd taberu-mate/frontend
npm install # 事前に Node.js をインストールしてください
```

### Step3 環境変数を設定
バックエンド:
```bash
cd ../backend
cp .env.example .env
```

フロントエンド:
```bash
cd ../frontend
cp .env.example .env.development
```

まずメニュー認識デモだけを動かしたい場合は、`backend/.env` にローカル Mock を設定します。
```bash
TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH="/Users/ariakage/Downloads/proj/taberu-mate/temp/1.json"
```

実際の AI サービスを呼び出す場合は、`backend/.env` に次の項目を追加してください。
```bash
TABERU_MATE_AI_API_KEY="your-api-key"
TABERU_MATE_AI_BASE_URL="https://api.openai.com/v1"
TABERU_MATE_AI_MODEL="gpt-5.5"
```

### Step4 バックエンドを起動
```bash
cd ../backend
uv run fastapi dev src/taberu_mate_backend/main.py --host 0.0.0.0 --port 8000
```

起動後、次の URL にアクセスできます。
- Swagger UI: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/api/v1/health

### Step5 フロントエンドを起動
別のターミナルを開きます。
```bash
cd taberu-mate/frontend
npm run dev
```

デフォルトのアクセス先:
- WebApp: http://127.0.0.1:5173/

### Step6 使い始める
1. フロントエンド WebApp を開く
2. 「我的」ページでアカウント登録またはログインを行う
3. ホームへ戻り、メニューを撮影またはアップロードする
4. 「点单」ページで料理を絞り込み、メモを入力して現地語の注文リストを生成する
5. 生成結果は「我的」ページの食事プロフィールとメニュー履歴に同期されます

## 🗂️ プロジェクト構成

このリポジトリは Monorepo 形式で、フロントエンド、バックエンド、ドキュメントを同じリポジトリ内に配置しています。

```
taberu-mate/
├── frontend/ # WebApp フロントエンド
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/ # API バックエンド (FastAPI)
│   ├── src/taberu_mate_backend
│   │   ├── main.py
│   │   └── ...
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
│
├── docs/ # プロジェクトドキュメント
├── .env.example
└── README.md
```

## 📖 使い方ドキュメント

### バックエンドサービスを起動

```bash
cd backend
cp .env.example .env
uv run fastapi dev src/taberu_mate_backend/main.py --host 0.0.0.0 --port 8000
```

起動後、次の URL にアクセスできます。

- Swagger UI: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/api/v1/health

### フロントエンド WebApp を起動

```bash
cd frontend
cp .env.example .env.development
npm run dev
```

デフォルトのアクセス先:

- WebApp: http://127.0.0.1:5173/

### ローカルメニュー認識 Mock

まだ実際の AI モデルを呼び出したくない場合は、バックエンド `.env` の mock パスをローカルのサンプルメニューに向けます。

```bash
TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH="/Users/ariakage/Downloads/proj/taberu-mate/temp/1.json"
```

この設定では、メニュー認識 API がサンプル JSON をそのまま返すため、フロントエンド連携やデモに便利です。

### さらに詳しいドキュメント

- バックエンド説明: [../backend/README.md](../backend/README.md)
- フロントエンド説明: [../frontend/README.md](../frontend/README.md)
- 認証フロー: [../backend/docs/auth-flow.md](../backend/docs/auth-flow.md)
- メニュー認識 API: [../backend/docs/menu-scan-api.md](../backend/docs/menu-scan-api.md)

## 🛠️ 設定

### バックエンド設定

バックエンド設定ファイルは `backend/.env` にあり、`backend/.env.example` からコピーして作成します。

よく使う設定項目:

- `TABERU_MATE_DATABASE_PATH`: SQLite データベースのパス
- `TABERU_MATE_AUTH_TOKEN_SECRET`: 認証用シークレット。デプロイ時は十分に長いランダム文字列へ変更してください
- `TABERU_MATE_AUTH_COOKIE_SECURE`: ローカル HTTP 開発では `false` に設定できます
- `TABERU_MATE_ALLOWED_ORIGINS`: バックエンドへのアクセスを許可するフロントエンド URL
- `TABERU_MATE_AI_API_KEY`: AI サービスの API Key
- `TABERU_MATE_AI_BASE_URL`: OpenAI API 互換サービスの URL
- `TABERU_MATE_AI_MODEL`: デフォルト AI モデル
- `TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH`: ローカルメニュー認識 Mock ファイルのパス

### フロントエンド設定

フロントエンド設定ファイルは `frontend/.env.development` にあり、`frontend/.env.example` からコピーして作成します。

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

この URL は単なるバックエンドのポートではなく、バックエンド API プレフィックスを指すようにしてください。

### よく使うチェックコマンド

バックエンド:

```bash
cd backend
uv run pytest
uv run ruff check .
uv run mypy src
```

フロントエンド:

```bash
cd frontend
npm run type-check
npm run test:unit -- --run
npm run build
```

## 🤝 コントリビューションガイド

Issue、提案、Pull Request を歓迎します。スムーズに協力するため、次の流れをおすすめします。

1. このリポジトリを Fork し、機能ブランチを作成する
2. コードを変更する前に、該当ディレクトリの README と docs を確認する
3. バックエンド機能には pytest のテストを追加する
4. フロントエンドの操作には Vitest またはコンポーネントテストを追加する
5. 提出前に該当ディレクトリのチェックコマンドを実行する
6. PR には変更の動機、主な実装、テスト結果を記載する

おすすめのコミットメッセージ形式:

```git
feat(menu): add AI menu scanning flow
fix(auth): handle expired access tokens
docs(readme): expand frontend setup guide
test(profile): cover order history dashboard
```

## 🙏 謝辞

食べ友をすばやく形にするため、次の素晴らしいプロジェクトに感謝します。

- [FastAPI](https://fastapi.tiangolo.com/): バックエンド API フレームワーク
- [Vue](https://vuejs.org/): フロントエンドアプリケーションフレームワーク
- [Vite](https://vite.dev/): フロントエンド開発・ビルドツール
- [Pinia](https://pinia.vuejs.org/): フロントエンド状態管理
- [Vant](https://vant-ui.github.io/vant/): モバイル向けコンポーネントライブラリ
- [Tailwind CSS](https://tailwindcss.com/): スタイルツールチェーン
- [uv](https://docs.astral.sh/uv/): Python 依存関係管理
- [OpenAI](https://openai.com/): AI 機能と OpenAI 互換 API エコシステム

## 🌟 スター数の履歴

<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="https://api.star-history.com/svg?repos=ariakage/taberu-mate&type=Date&theme=dark"
  />
  <source
    media="(prefers-color-scheme: light)"
    srcset="https://api.star-history.com/svg?repos=ariakage/taberu-mate&type=Date"
  />
  <img
    alt="Star History Chart"
    src="https://api.star-history.com/svg?repos=ariakage/taberu-mate&type=Date"
  />
</picture>

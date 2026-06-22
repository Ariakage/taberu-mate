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
  <a href="../README.md">简体中文</a> | English | <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <a href="https://github.com/ariakage/taberu-mate">
    <img src="assets/header.png" alt="TaberuMate Logo" />
  </a>
  <br />
  <strong>TaberuMate -- fear no unfamiliar menu, and eat well wherever you travel.</strong>
</p>

## ✨ Features

- **📷 One-shot menu recognition**

  Take a photo of a restaurant menu with your phone, and AI turns it into an interactive digital menu without manual input

- **🍽️ Scan-to-order / delivery-style ordering experience**

  Browse dishes, images, prices, and descriptions with a familiar ordering flow, with multilingual switching supported

- **🌍 Smart translation into local languages**

  Use an agent to translate menus into your native language or the language of your destination, supporting 100+ languages with natural results

- **🌟 Smart filters and dietary notes**

  Filter by taste, price, spice level, vegetarian options, and more; add dietary restrictions just like order notes

- **🔏 Privacy and safety**

  Quickly self-host your own lightweight platform and keep the workflow under your control

## 🚀 Quick Start

### Step1 Clone the repository
```bash
git clone https://github.com/Ariakage/taberu-mate.git
```

### Step2-1 Set up the Python environment
```bash
cd taberu-mate/backend
uv sync # Install uv as the package manager first
```

### Step2-2 Set up the Vue environment
```bash
cd taberu-mate/frontend
npm install # Install Node.js first
```

### Step3 Configure environment variables
Backend:
```bash
cd ../backend
cp .env.example .env
```

Frontend:
```bash
cd ../frontend
cp .env.example .env.development
```

If you only want to run the menu recognition demo first, configure the local mock in `backend/.env`:
```bash
TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH="/Users/ariakage/Downloads/proj/taberu-mate/temp/1.json"
```

If you want to call a real AI service, add the following to `backend/.env`:
```bash
TABERU_MATE_AI_API_KEY="your-api-key"
TABERU_MATE_AI_BASE_URL="https://api.openai.com/v1"
TABERU_MATE_AI_MODEL="gpt-5.5"
```

### Step4 Start the backend
```bash
cd ../backend
uv run fastapi dev src/taberu_mate_backend/main.py --host 0.0.0.0 --port 8000
```

After startup, visit:
- Swagger UI: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/api/v1/health

### Step5 Start the frontend
Open another terminal:
```bash
cd taberu-mate/frontend
npm run dev
```

Default URL:
- WebApp: http://127.0.0.1:5173/

### Step6 Start using it
1. Open the frontend WebApp
2. Register or sign in from the "Mine" page
3. Return to the home page and take or upload a menu photo
4. Filter dishes, add notes, and generate a local-language order list from the "Order" page
5. Generated results are synced to the meal profile and menu history on the "Mine" page

## 🗂️ Project Structure

This repository uses a monorepo layout, with the frontend, backend, and documentation stored under the same project root.

```
taberu-mate/
├── frontend/ # WebApp frontend
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/ # API backend (FastAPI)
│   ├── src/taberu_mate_backend
│   │   ├── main.py
│   │   └── ...
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
│
├── docs/ # Project documentation
├── .env.example
└── README.md
```

## 📖 Usage Docs

### Start the backend service

```bash
cd backend
cp .env.example .env
uv run fastapi dev src/taberu_mate_backend/main.py --host 0.0.0.0 --port 8000
```

After startup, visit:

- Swagger UI: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/api/v1/health

### Start the frontend WebApp

```bash
cd frontend
cp .env.example .env.development
npm run dev
```

Default URL:

- WebApp: http://127.0.0.1:5173/

### Local menu recognition mock

If you do not want to call a real AI model yet, point the mock path in backend `.env` to the local sample menu:

```bash
TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH="/Users/ariakage/Downloads/proj/taberu-mate/temp/1.json"
```

The menu recognition endpoint will return the sample JSON directly, which is useful for frontend integration and demos.

### More docs

- Backend guide: [../backend/README.md](../backend/README.md)
- Frontend guide: [../frontend/README.md](../frontend/README.md)
- Auth flow: [../backend/docs/auth-flow.md](../backend/docs/auth-flow.md)
- Menu scan API: [../backend/docs/menu-scan-api.md](../backend/docs/menu-scan-api.md)

## 🛠️ Configuration

### Backend configuration

The backend configuration file is `backend/.env`, copied from `backend/.env.example`.

Common options:

- `TABERU_MATE_DATABASE_PATH`: SQLite database path
- `TABERU_MATE_AUTH_TOKEN_SECRET`: Authentication secret; replace it with a long random string before deployment
- `TABERU_MATE_AUTH_COOKIE_SECURE`: Set to `false` for local HTTP development
- `TABERU_MATE_ALLOWED_ORIGINS`: Frontend origins allowed to access the backend
- `TABERU_MATE_AI_API_KEY`: AI service API key
- `TABERU_MATE_AI_BASE_URL`: OpenAI-compatible API base URL
- `TABERU_MATE_AI_MODEL`: Default AI model
- `TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH`: Local menu recognition mock file path

### Frontend configuration

The frontend configuration file is `frontend/.env.development`, copied from `frontend/.env.example`.

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Make sure this URL points to the backend API prefix, not only the backend port.

### Common check commands

Backend:

```bash
cd backend
uv run pytest
uv run ruff check .
uv run mypy src
```

Frontend:

```bash
cd frontend
npm run type-check
npm run test:unit -- --run
npm run build
```

## 🤝 Contribution Guide

Issues, suggestions, and pull requests are welcome. For smoother collaboration, we recommend the following flow:

1. Fork this repository and create a feature branch
2. Check the README and docs in the related directory before changing code
3. Add pytest coverage for backend features
4. Add Vitest or component tests for frontend interactions
5. Run the corresponding check commands before submitting
6. Describe the motivation, implementation, and test results in the PR

Recommended commit message format:

```git
feat(menu): add AI menu scanning flow
fix(auth): handle expired access tokens
docs(readme): expand frontend setup guide
test(profile): cover order history dashboard
```

## 🙏 Thanks

Thanks to these excellent projects for making TaberuMate quick to build:

- [FastAPI](https://fastapi.tiangolo.com/): Backend API framework
- [Vue](https://vuejs.org/): Frontend application framework
- [Vite](https://vite.dev/): Frontend development and build tool
- [Pinia](https://pinia.vuejs.org/): Frontend state management
- [Vant](https://vant-ui.github.io/vant/): Mobile component library
- [Tailwind CSS](https://tailwindcss.com/): Styling toolchain
- [uv](https://docs.astral.sh/uv/): Python dependency management
- [OpenAI](https://openai.com/): AI capabilities and OpenAI-compatible API ecosystem

## 🌟 Star History

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

<h1 align="center">TaberuMate - Backend<br/><a href="../LICENSE">
    <img src="https://img.shields.io/badge/license-AGPL--3.0--only-blue.svg?style=flat-square" alt="License: AGPL-3.0-only" />
  </a><a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.13+" />
  </a><a href="https://docs.astral.sh/uv/">
    <img src="https://img.shields.io/badge/package%20manager-uv-261230?style=flat-square" alt="uv" />
  </a></h1>

## Overview

This directory contains the FastAPI backend for TaberuMate. It provides authentication, CSRF-protected session handling, AI chat, menu-image recognition, user food profiles, and order-history persistence.

The service uses SQLite for local development and initializes its tables automatically on app startup.

## QuickStart

```bash
uv sync
cp .env.example .env
uv run fastapi dev src/taberu_mate_backend/main.py --host 0.0.0.0 --port 8000
```

API docs:

- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/v1/health
- Auth flow: [docs/auth-flow.md](docs/auth-flow.md)
- Menu scan API: [docs/menu-scan-api.md](docs/menu-scan-api.md)

## What The Backend Does

- Authenticates users with access tokens, refresh tokens, HttpOnly cookies, bearer headers, and CSRF tokens.
- Stores users, refresh tokens, access-token revocations, food profiles, and order history in SQLite.
- Calls an OpenAI-compatible chat completions API for general AI chat and menu-specific vision prompts.
- Streams menu recognition responses to the frontend through server-sent events.
- Supports a local mock JSON file for menu recognition during frontend demos and tests.
- Exposes user dashboard data for the frontend home/profile screens.

## Environment

Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

Important variables:

| Variable | Purpose |
| --- | --- |
| `TABERU_MATE_DATABASE_PATH` | SQLite database path. Defaults to `data/taberu_mate.db`. |
| `TABERU_MATE_AUTH_TOKEN_SECRET` | Secret used for auth token signing. Replace for real deployments. |
| `TABERU_MATE_AUTH_COOKIE_SECURE` | Set `false` for plain local HTTP, `true` for HTTPS. |
| `TABERU_MATE_ALLOWED_ORIGINS` | Explicit CORS origins for the frontend. |
| `TABERU_MATE_ALLOWED_ORIGIN_REGEX` | Regex-based CORS origins, useful for Vite ports. |
| `TABERU_MATE_AI_API_KEY` | API key for the configured AI provider. |
| `TABERU_MATE_AI_BASE_URL` | OpenAI-compatible base URL. |
| `TABERU_MATE_AI_MODEL` | Default model used by AI chat and menu scan. |
| `TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH` | Optional local menu JSON used instead of calling AI. |

## Main API Surface

All routes are prefixed by `/api/v1` by default.

| Area | Routes | Notes |
| --- | --- | --- |
| Health | `GET /health` | Basic service status. |
| Auth | `GET /auth/csrf`, `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` | State-changing auth routes require CSRF. |
| User | `GET /users/me` | Current authenticated user. |
| Food profile | `GET /users/me/profile`, `PUT /users/me/profile` | Saves avoidances, allergies, and notes. |
| Order history | `GET /users/me/orders`, `POST /users/me/orders` | Saves generated order sheets and selected items. |
| Dashboard | `GET /users/me/dashboard` | Combines profile stats and recent orders. |
| AI chat | `POST /ai/chat` | Authenticated generic AI chat endpoint. |
| Menu scan | `POST /menus/scan`, `POST /menus/scan/stream` | Authenticated menu image recognition. |

## Authentication Notes

1. Call `GET /api/v1/auth/csrf` and keep the returned `csrf_token`.
2. Send `X-CSRF-Token` for state-changing requests such as register, login, logout, profile update, and order-history creation.
3. Login returns an access token and also sets auth cookies.
4. The frontend stores the access token for bearer requests and relies on refresh-token rotation when access expires.

See [docs/auth-flow.md](docs/auth-flow.md) for more detail.

## AI Chat

Set these values in `.env`:

```bash
TABERU_MATE_AI_API_KEY="your-api-key"
TABERU_MATE_AI_BASE_URL="https://api.openai.com/v1"
TABERU_MATE_AI_MODEL="gpt-5.5"
```

`POST /api/v1/ai/chat` requires an authenticated user and returns the raw Chat Completions response format.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ai/chat \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "You are a restaurant ordering assistant.",
    "message": "Generate a short dinner suggestion.",
    "response_format": "json_object"
  }'
```

## Menu Scan Mock Output

During frontend or API testing, the menu scan service can read a local JSON file instead of calling the configured AI model. Set this value in `.env`:

```bash
TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH="/Users/ariakage/Downloads/proj/taberu-mate/temp/1.json"
```

Then restart the backend:

```bash
uv run fastapi dev src/taberu_mate_backend/main.py --host 0.0.0.0 --port 8000
```

When this value is set, both `POST /api/v1/menus/scan` and `POST /api/v1/menus/scan/stream` still require login and a bearer token, but they return the mock file content as the menu recognition result. The mock file may be raw menu JSON matching the menu scan schema, or a Chat Completions-style response containing `choices[0].message.content`.

To disable the mock and call the configured model again, remove the variable or leave it empty, then restart the backend:

```bash
TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH=""
```

## Database

The app creates and migrates local SQLite tables during startup through `init_db()`:

- `users`
- `refresh_tokens`
- `access_token_revocations`
- `user_profiles`
- `order_history`

For local development, deleting `data/taberu_mate.db` resets the database. Do this only when you are comfortable losing local users and history.

## Project Layout

```text
src/taberu_mate_backend/
├── api/
│   ├── deps.py          # auth, CSRF, and service dependencies
│   ├── router.py        # API router composition
│   └── routes/          # health, users, AI, menus
├── core/                # settings, security, rate limiting, errors
├── crud/                # SQLite data access helpers
├── db/                  # connection and schema initialization
├── models/              # internal dataclasses
├── schemas/             # Pydantic request/response models
├── services/            # AI service and business logic
└── main.py              # FastAPI app factory
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

If a restricted environment cannot write to the default uv cache, use a temporary cache:

```bash
UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest
```

## Troubleshooting

- `401 Invalid credentials`: login again or check the bearer token.
- `403 Invalid CSRF token`: call `/auth/csrf` and send `X-CSRF-Token` on state-changing requests.
- `503 AI service is not configured`: set `TABERU_MATE_AI_API_KEY` or use `TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH`.
- Frontend CORS issues: verify `TABERU_MATE_ALLOWED_ORIGINS` or `TABERU_MATE_ALLOWED_ORIGIN_REGEX`.
- Secure cookie issues on plain HTTP: set `TABERU_MATE_AUTH_COOKIE_SECURE=false` for local development.

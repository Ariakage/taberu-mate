<h1 align="center">TaberuMate - Backend<br/><a href="LICENSE">
    <img src="https://img.shields.io/badge/license-AGPL--3.0--only-blue.svg?style=flat-square" alt="License: AGPL-3.0-only" />
  </a><a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.13+" />
  </a><a href="https://docs.astral.sh/uv/">
    <img src="https://img.shields.io/badge/package%20manager-uv-261230?style=flat-square" alt="uv" />
  </a></h1>

## 🚀 QuickStart
```bash
uv sync
cp .env.example .env
uv run fastapi dev src/taberu_mate_backend/main.py
```

API docs:

- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/v1/health
- Auth flow: [docs/auth-flow.md](docs/auth-flow.md)

## Project Layout

```text
src/taberu_mate_backend/
├── api/          # API routers and route handlers
├── core/         # App settings and shared core utilities
├── crud/         # Data access helpers
├── db/           # Database session and migrations entry points
├── models/       # ORM models
├── schemas/      # Pydantic request/response schemas
├── services/     # Business logic
├── utils/        # General-purpose helpers
└── main.py       # FastAPI app factory and ASGI app
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

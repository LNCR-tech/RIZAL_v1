# Repository Layout

<!--nav-->
[Previous](ports.md) | [Next](../../README.md) | [Home](/README.md)

---
<!--/nav-->

## Top-Level Folders

- `backend/` — FastAPI API, Alembic migrations, Celery workers/beat, and the production bootstrap script
- `assistant/` — Streaming LLM assistant with MCP tool integration
- `frontend-web/` — Vue 3 (Vite) SPA plus Capacitor mobile
- `frontend-apk/` — Capacitor Android native project
- `database/` — Postgres service, schema docs, Docker init scripts
- `seeder/` — Demo data seeder (dev only)
- `backend/docs/` — Backend and platform operations documentation
- `frontend-web/docs/` — Frontend and user-facing documentation

## Key Top-Level Files

- `backend/.env.example`, `assistant/.env.example`, `database/.env.example`, `frontend-web/.env.example`, `seeder/.env.example` — per-service configuration templates
- `docker-compose.yml` — full stack with Postgres, Redis, migrations, bootstrap, backend, assistant, frontend, seeder, and dev tools
- `README.md` — entry point with links into service docs folders

# Repository Layout

<!--nav-->
[Previous](ports.md) | [Next](../../README.md) | [Home](/README.md)

---
<!--/nav-->

## Top-Level Folders

- `backend/`: FastAPI API, Alembic migrations, Celery workers/beat, and the production bootstrap script
- `assistant/`: Active assistant service
- `frontend/`: Vue 3 (Vite) SPA plus Capacitor assets
- `backend/docs/`: Backend and platform operations documentation
- `frontend/docs/`: Frontend and user-facing documentation
- `docker-init/`: Postgres init scripts mounted by the local Docker stack

## Key Top-Level Files

- `.env.example`: Minimal configuration template for secrets, connection strings, public URLs, and operational overrides
- `docker-compose.yml`: Local Docker stack with Postgres, Redis, migrations, backend, assistant, frontend, and pgAdmin
- `README.md`: Entry point with links into service docs folders


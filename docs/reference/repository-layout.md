# Repository Layout

[<- Back to docs index](../../README.md)

## Top-Level Folders

- `Backend/`: FastAPI API, Alembic migrations, Celery workers/beat, seed scripts.
- `Assistant-v1/`: Legacy assistant service.
- `Assistant-v2/`: Active assistant service.
- `Frontend/`: Vue 3 (Vite) SPA + Capacitor (Android).
- `docs/`: Documentation (this folder).
- `docker-init/`: Postgres init scripts mounted by Docker.

## Key Top-Level Files

- `.env.example`: Configuration template for local and Docker runs.
- `docker-compose.yml`: Local Docker stack (db, backend, assistant, frontend, redis, mailpit, pgadmin).
- `docker-compose.prod.yml`: Production-ish compose (if used in your deployment flow).
- `README.md`: Entry point with links to `docs/`.



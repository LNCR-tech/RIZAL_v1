# Repository Layout

[<- Back to docs index](../../README.md)

## Top-Level Folders

- `Backend/`: FastAPI API, Alembic migrations, Celery workers/beat, and the production bootstrap script
- `Assistant-v2/`: Active assistant service
- `Frontend/`: Vue 3 (Vite) SPA plus Capacitor assets
- `docs/`: Documentation
- `docker-init/`: Postgres init scripts mounted by the local Docker stack

## Key Top-Level Files

- `.env.example`: Minimal configuration template for secrets, connection strings, public URLs, and operational overrides
- `docker-compose.yml`: Local Docker stack with Postgres, Redis, migrations, backend, assistant, frontend, and pgAdmin
- `README.md`: Entry point with links into `docs/`

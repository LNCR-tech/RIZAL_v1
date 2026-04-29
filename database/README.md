# Database Service

<!--nav-->
[Previous](../README.md) | [Next](db_normalized/db_schema.md) | [Home](/README.md)

---
<!--/nav-->

Postgres service for Aura. Contains the init scripts, normalized schema design docs, and its own Dockerfile and docker-compose for standalone use.

## Contents

- `Dockerfile` — extends `pgvector/pgvector:pg15` with the init scripts baked in
- `docker-compose.yml` — standalone Postgres + pgAdmin stack
- `docker-init/` — SQL scripts run on first Postgres container startup
- `db_normalized/` — normalized schema design, ERD, and migration planning docs
- `.env.example` — environment variable template

## Setup

```bash
cp .env.example .env
# fill in POSTGRES_USER, POSTGRES_PASSWORD
```

## Standalone Usage

```bash
cd database
docker compose up --build
```

## Full Stack Usage

For the full Aura stack, use the root `docker-compose.yml` instead:

```bash
# from repo root
docker compose --profile dev up --build
```

## Notes

- Both `fastapi_db` and `ai_assistant` databases are created automatically by `docker-init/init.sql` on first container startup.
- Alembic migrations live in `backend/alembic/` since they depend on the SQLAlchemy models in `backend/app/models/`.
- To run migrations: `cd ../backend && alembic upgrade head`
- pgAdmin is available at `http://localhost:5050` when running standalone or in the dev profile.

## Docs

- [Normalized DB Schema](db_normalized/db_schema.md)

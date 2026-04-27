# Database Service

Postgres service for Aura. Also contains the normalized schema design docs and Docker init scripts.

## Contents

- `docker-init/` — SQL scripts run on first Postgres container startup
- `db_normalized/` — normalized schema design, ERD, and migration planning docs
- `.env.example` — environment variable template

## Setup

```bash
cp .env.example .env
# fill in POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
```

## Notes

- Alembic migrations live in `backend/alembic/` since they depend on the SQLAlchemy models in `backend/app/models/`
- To run migrations: `cd ../backend && alembic upgrade head`
- pgAdmin is available at `http://localhost:5050` in the Docker dev stack (not for production)

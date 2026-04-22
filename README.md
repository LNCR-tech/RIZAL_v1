# Aura (Student Attendance System)

Aura is a student attendance system with:

- `Backend/`: FastAPI API, Alembic migrations, Celery workers, bootstrap and demo seed scripts
- `Assistant-v2/`: the active assistant service backed by Postgres
- `Frontend/`: Vue 3 (Vite) SPA plus optional Capacitor assets

## Quick Start (Docker)

### First-time setup (run once on a fresh machine)

```powershell
# 1. Copy and configure environment
Copy-Item .\.env.example .\.env -Force
notepad .\.env

# 2. Build images and start infrastructure (db + redis)
docker compose up --build -d db redis

# 3. Run database migrations
docker compose run --rm -e DATABASE_URL=postgresql://postgres:postgres@db:5432/fastapi_db backend alembic upgrade heads

# 4. Bootstrap admin account (creates only the admin user + default school)
docker compose run --rm -e DATABASE_URL=postgresql://postgres:postgres@db:5432/fastapi_db backend python bootstrap.py --admin-email admin@yourdomain.com --admin-password YourPassword123!

# 5. Start all services
docker compose up -d
```

### Subsequent starts (already set up)

```powershell
docker compose up -d
```

Open:

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- Assistant docs (via frontend proxy): `http://localhost:5173/__assistant__/docs`
Email delivery is disabled by default (`EMAIL_TRANSPORT=disabled`). Set to `mailjet_api` and provide `MAILJET_API_KEY` / `MAILJET_API_SECRET` in `.env` to enable it.

## Production Path

This repository uses a single compose file: `docker-compose.yml`.

For a production-style rollout on a fresh machine:

```powershell
# 1. Build and start infrastructure
docker compose up --build -d db redis

# 2. Run migrations
docker compose run --rm -e DATABASE_URL=postgresql://postgres:postgres@db:5432/fastapi_db backend alembic upgrade heads

# 3. Bootstrap the admin account
docker compose run --rm backend python bootstrap.py --admin-email <email> --admin-password <password>

# 4. Start all services
docker compose up -d backend worker beat assistant frontend
```

## Documentation

Start here:

- [Getting Started (Docker)](./docs/getting-started/docker.md)
- [Getting Started (Local Dev, no Docker)](./docs/getting-started/local-dev.md)
- [Common Commands](./docs/reference/common-commands.md)
- [Environment Variables](./docs/reference/env.md)
- [Ports and URLs](./docs/reference/ports.md)
- [Repository Layout](./docs/reference/repository-layout.md)

Component docs:

- [Backend docs](./docs/backend/README.md)
- [Frontend docs](./docs/frontend/README.md)
- [Assistant docs](./docs/assistant/README.md)

Product docs:

- [Aura Overview](./docs/user/overview.md)
- [Navigation Map](./docs/user/navigation.md)

Audits:

- [Audit Report](./docs/audits/AUDIT_REPORT.md)
- [Project Audit](./docs/audits/project_audit.md)

## Notes

- Redis/Celery is optional for a bare API boot, but background jobs require Redis plus worker/beat.
- Non-secret backend defaults live in `Backend/app/core/app_settings.py`.
- Non-secret assistant defaults live in `Assistant-v2/lib/app_settings.py`.

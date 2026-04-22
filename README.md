# Aura (Student Attendance System)

Aura is a student attendance system with:

- `Backend/`: FastAPI API + Alembic migrations + Celery tasks
- `Assistant-v2/` (active) and `Assistant-v1/` (legacy): assistant services backed by Postgres
- `Frontend/`: Vue 3 (Vite) SPA + optional Capacitor (Android)

## Quick Start (Docker)

```powershell
Copy-Item .\\.env.example .\\.env -Force
notepad .\\.env
docker compose up --build
```

Open:

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- Assistant docs (via frontend proxy): `http://localhost:5173/__assistant__/docs`
- pgAdmin (DB): `http://localhost:5050` (admin@example.com / admin123)
- Mailpit (Email): `http://localhost:8025`

## Documentation

Start here:

- [Getting Started (Docker)](./docs/getting-started/docker.md)
- [Getting Started (Local Dev, no Docker)](./docs/getting-started/local-dev.md)
- [Common Commands](./docs/reference/common-commands.md)
- [Environment Variables](./docs/reference/env.md)
- [Ports and URLs](./docs/reference/ports.md)
- [Repository Layout](./docs/reference/repository-layout.md)

Components:

- [Backend docs](./docs/backend/README.md)
- [Frontend docs](./docs/frontend/README.md)
- [Assistant docs](./docs/assistant/README.md)

Product (Non-Developer):

- [Aura Overview](./docs/user/overview.md)
- [Navigation Map](./docs/user/navigation.md)

Audits:

- [Audit Report](./docs/audits/AUDIT_REPORT.md)
- [Project Audit](./docs/audits/project_audit.md)

## Notes

- Redis/Celery: the API can start without Redis, but features that enqueue background jobs require Redis + a Celery worker/beat.
- If your DB has a stale `alembic_version` from a different migration history, dropping/recreating the DB is often faster than untangling the revision graph.

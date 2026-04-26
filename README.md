# Aura (Student Attendance System)

⚠️ **SECURITY ALERT**: Critical security issues found and fixed. Review [SECURITY_ALERT.md](SECURITY_ALERT.md) before deployment.

Aura is a student attendance system with:

- `backend/`: FastAPI API, Alembic migrations, Celery workers, and the production bootstrap script
- `assistant/`: the active assistant service backed by Postgres
- `frontend/`: Vue 3 (Vite) SPA plus optional Capacitor assets

## Quick Start (Docker)

⚠️ **SECURITY NOTICE**: Before production deployment, complete [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md).

```powershell
# 1. Copy and configure environment
Copy-Item .\.env.example .\.env -Force
notepad .\.env

# 2. Set SECRET_KEY, AI_API_KEY, AI_API_BASE, AI_MODEL in .env

# 3. Start everything
docker compose up --build
```

Migrations, bootstrap, and all services start automatically. When ready:

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- Assistant docs: `http://localhost:8500/docs`
- Mailpit (email capture): `http://localhost:8025`
- pgAdmin: `http://localhost:5050`

Email delivery is disabled by default (`EMAIL_TRANSPORT=disabled`). Set to `mailjet_api` and provide `MAILJET_API_KEY` / `MAILJET_API_SECRET` in `.env` to enable it.
For local capture testing, set `EMAIL_TRANSPORT=smtp` with `SMTP_HOST=mailpit` and open Mailpit at `http://localhost:8025`.

## Production Path

Update these variables in `.env` before deploying to a server:

- `SECRET_KEY` — use a long random string
- `DATABASE_URL` / `ASSISTANT_DB_URL` — point to your production Postgres
- `LOGIN_URL` / `CORS_ALLOWED_ORIGINS` — your frontend's public URL
- `BACKEND_ORIGIN` / `BACKEND_API_BASE_URL` — your backend's public URL
- `ASSISTANT_ORIGIN` — your assistant's public URL
- `EMAIL_TRANSPORT` — set to `mailjet_api`
- `MAILJET_API_KEY` — your Mailjet API key
- `MAILJET_API_SECRET` — your Mailjet API secret
- `UVICORN_WORKERS` — increase for production
- `FRONTEND_PORT` — change to `80` or `443`

Then run the same single command:

```powershell
docker compose up --build
```

## Documentation

Security (READ FIRST):

- [🚨 Security Alert](SECURITY_ALERT.md) - CRITICAL: Immediate actions required
- [Security Audit Summary](SECURITY_AUDIT_SUMMARY.md) - Overview of findings and fixes
- [Security Checklist](SECURITY_CHECKLIST.md) - Pre-deployment checklist
- [Security Hardening Guide](docs/SECURITY_HARDENING.md) - Architecture and best practices

Start here:

- [How to Run (all platforms)](./docs/getting-started/how-to-run.md)
- [Getting Started (Docker)](./docs/getting-started/docker.md)
- [Getting Started (Local Dev, no Docker)](./docs/getting-started/local-dev.md)
- [Deploying to Linux / AWS](./docs/getting-started/linux-deploy.md)
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
- Non-secret backend defaults live in `backend/app/core/app_settings.py`.
- Non-secret assistant defaults live in `assistant/lib/app_settings.py`.

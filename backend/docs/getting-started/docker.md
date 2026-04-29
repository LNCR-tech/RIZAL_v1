# Getting Started (Docker)

<!--nav-->
[Previous](../../README.md) | [Next](how-to-run.md) | [Home](/README.md)

---
<!--/nav-->

This is the fastest way to run the full system locally from the repo root.

## Prerequisites

- Docker Desktop installed and running

## Which Env File Goes Where

- Root `.env`
  Used by repo-root `docker compose`
- `frontend/.env.docker`
  Only for the standalone frontend-only Docker setup inside `frontend/`

For the normal repo-root Docker flow, you only need the root `.env`.

## Steps

1. Create `.env`:

```powershell
Copy-Item .\.env.example .\.env -Force
notepad .\.env
```

2. Set the required shared values:

- `SECRET_KEY`
- `AI_API_KEY`
- `AI_API_BASE`
- `AI_MODEL`

3. Start the stack:

```powershell
docker compose up --build
```

That's it. Migrations, bootstrap, and all services start automatically in the correct order. When the stack is ready you'll see a summary printed in the logs:

```
-------------------------------------------------------
   AURA SYSTEM IS READY!
-------------------------------------------------------
Frontend:        http://localhost:5173
Backend API:     http://localhost:8000/docs
Assistant API:   http://localhost:8500/docs
pgAdmin (DB):    http://localhost:5050 (admin@example.com / admin123)
Mailpit (Email): http://localhost:8025
Logs:            http://localhost:8088
-------------------------------------------------------
```

## Startup Order

The compose file handles this automatically:

```
db (healthy)
  â””â”€â”€ migrate        (alembic upgrade heads)
        â””â”€â”€ bootstrap  (python bootstrap.py â€” seeds roles, event types, admin)
              â””â”€â”€ backend / worker / beat
                    â””â”€â”€ frontend / assistant
```

## Notes

- Running `docker compose up --build` multiple times is safe â€” migrations and bootstrap are both idempotent.
- Local container logs are available in the log viewer at `http://localhost:8088`. It reads Docker container stdout/stderr through the read-only Docker socket mount in the `log-viewer` service.
- Terminal log access is still available with `docker compose logs -f` for all services or `docker compose logs -f backend` for only the backend API server.
- Email delivery is disabled by default (`EMAIL_TRANSPORT=disabled`). For local email capture, set `EMAIL_TRANSPORT=smtp` with `SMTP_HOST=mailpit` and open Mailpit at `http://localhost:8025`. For production, use `EMAIL_TRANSPORT=mailjet_api` with `MAILJET_API_KEY` and `MAILJET_API_SECRET`.
- The default admin credentials are set in `backend/app/core/app_settings.py` (`default_admin_email` / `default_admin_password`).
- The repo-root `docker-compose.yml` defaults to the local Postgres container, but honors `DATABASE_URL` and `ASSISTANT_DB_URL` from `.env` when you need to point the stack at an external Postgres host.

## Moving to Production

Change these variables in `.env` before deploying:

| Variable | Why |
|---|---|
| `SECRET_KEY` | Use a long random string â€” never the dev placeholder |
| `DATABASE_URL` | Point to your production Postgres host |
| `ASSISTANT_DB_URL` | Same |
| `LOGIN_URL` | Your frontend's public URL |
| `CORS_ALLOWED_ORIGINS` | Same as `LOGIN_URL` |
| `BACKEND_API_BASE_URL` | Your backend's public URL |
| `BACKEND_ORIGIN` | Your backend's public URL â€” used by the frontend NGINX container to proxy `/__backend__/` requests |
| `ASSISTANT_ORIGIN` | Your assistant's public URL |
| `EMAIL_TRANSPORT` | Set to `mailjet_api` for production |
| `MAILJET_API_KEY` | Your Mailjet API key |
| `MAILJET_API_SECRET` | Your Mailjet API secret |
| `UVICORN_WORKERS` | Increase to match your CPU count |
| `FRONTEND_PORT` | Change from `5173` to `80` or `443` |


# Getting Started (Docker)

[<- Back to docs index](../../README.md)

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

4. Open the app:

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`

## Notes

- Use `python backend/bootstrap.py --admin-email ... --admin-password ...` after migrations to create the first platform admin.
- Email delivery is disabled by default. If you want real outbound email, configure SMTP or Mailjet in the root `.env`.
- The current repo-root `docker-compose.yml` is local-stack oriented and hardcodes local container URLs for Postgres, Redis, backend, and assistant. For external production infra, use a compose override or edit the compose file.

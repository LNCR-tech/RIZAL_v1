# Getting Started (Docker)

[<- Back to docs index](../../README.md)

This is the fastest way to run the full system locally: Postgres, Redis, backend, assistant, frontend, and pgAdmin.

## Prerequisites

- Docker Desktop installed and running

## Steps

1. Create `.env`:

```powershell
Copy-Item .\.env.example .\.env -Force
notepad .\.env
```

2. Start the stack:

```powershell
docker compose up --build
```

3. Open the app:

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- Assistant docs (via frontend proxy): `http://localhost:5173/__assistant__/docs`
- pgAdmin: `http://localhost:5050`

## Notes

- Use `python backend/bootstrap.py --admin-email ... --admin-password ...` after migrations to create the first platform admin.
- Email delivery is disabled by default. If you want real outbound email, configure Mailjet in `.env`.
- Production uses the same `docker-compose.yml` file with explicit migration and bootstrap commands.

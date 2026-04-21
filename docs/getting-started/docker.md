# Getting Started (Docker)

[<- Back to docs index](../../README.md)

This is the fastest way to run the full system locally (DB, migrations, seed, backend, assistant, frontend).

## Prerequisites

- Docker Desktop installed and running.

## Steps

1. Create `.env`:

```powershell
Copy-Item .\\.env.example .\\.env -Force
notepad .\\.env
```

See: [Environment Variables](../reference/env.md).

2. Start the stack:

```powershell
docker compose up --build
```

3. Open the app:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000/docs`
- Assistant (via frontend proxy): `http://localhost:5173/__assistant__/docs`

For the full list, see: [Ports and URLs](../reference/ports.md).

## Optional: Local Email Testing (Mailpit)

See: [Backend Email Delivery Guide](../backend/BACKEND_EMAIL_LOCAL_TESTING_GUIDE.md).


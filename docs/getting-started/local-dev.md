# Getting Started (Local Dev, no Docker)

[<- Back to docs index](../../README.md)

This runs each service directly on your machine for debugging and faster iteration.

## Prerequisites

- Python for backend and assistant
- PostgreSQL with `fastapi_db` and `ai_assistant`
- Redis
- Node.js and npm

## Which Env File Goes Where

- Root `.env`
  Backend, assistant, and worker/beat settings.
- `frontend/.env.development.local`
  Frontend Vite dev settings only.

Create them from:

- `.env.example`
- `frontend/.env.development.local.example`

## Required Root `.env` Values

- `SECRET_KEY`
- `AI_API_KEY`
- `AI_API_BASE`
- `AI_MODEL`
- `DATABASE_URL`
- `ASSISTANT_DB_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `BACKEND_API_BASE_URL=http://127.0.0.1:8000`

## Required Frontend Local Override

```env
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8000
```

Optional frontend local values:

```env
VITE_API_BASE_URL=/__backend__
VITE_API_TIMEOUT_MS=15000
```

## Startup Order

Start services in this order to avoid startup warnings:

1. PostgreSQL
2. Redis
3. Mailpit (if `EMAIL_TRANSPORT=smtp`)
4. Backend
5. Assistant
6. Frontend

The backend will start even if Mailpit is not running — it logs a warning and continues. But email delivery will fail silently until Mailpit is up.

## Steps

1. Copy `.env.example` to `.env` and point the connection strings at your local services.
2. Copy `frontend/.env.development.local.example` to `frontend/.env.development.local`.
3. Run backend migrations.
4. Run the explicit bootstrap command.
5. Start backend, assistant, and frontend.

The canonical commands are in [Common Commands](../reference/common-commands.md).

## Redis on WSL

If you run Redis inside WSL, the broker URLs in `.env` must point at the WSL IP, not `127.0.0.1`:

```env
CELERY_BROKER_URL=redis://<wsl-ip>:6379/0
CELERY_RESULT_BACKEND=redis://<wsl-ip>:6379/0
```

Get your current WSL IP:

```bash
wsl hostname -I
```

This IP changes every time you reboot your laptop. Re-run the command after each reboot and update `.env` if Celery fails to connect.

## Verification URLs

See: [Ports and URLs](../reference/ports.md).

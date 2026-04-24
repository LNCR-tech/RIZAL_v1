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

## Steps

1. Copy `.env.example` to `.env` and point the connection strings at your local services.
2. Copy `frontend/.env.development.local.example` to `frontend/.env.development.local`.
3. Run backend migrations.
4. Run the explicit bootstrap command.
5. Start backend, assistant, and frontend.

The canonical commands are in [Common Commands](../reference/common-commands.md).

## Verification URLs

See: [Ports and URLs](../reference/ports.md).

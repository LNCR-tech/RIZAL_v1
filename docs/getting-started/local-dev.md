# Getting Started (Local Dev, no Docker)

[<- Back to docs index](../../README.md)

This runs each service directly on your machine for debugging and faster iteration.

## Prerequisites

- Python for backend and assistant
- PostgreSQL with `fastapi_db` and `ai_assistant`
- Redis
- Node.js and npm

## Steps

1. Create `.env` from `.env.example` and point the connection strings at your local services.
2. Run backend migrations.
3. Run the explicit bootstrap command.
4. Start backend, assistant, and frontend.

The canonical commands are in [Common Commands](../reference/common-commands.md).

## Frontend Local Override

For manual frontend dev, create `Frontend/.env.development.local`:

```env
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8000
VITE_ASSISTANT_PROXY_TARGET=http://127.0.0.1:8500
VITE_ASSISTANT_BASE_URL=http://127.0.0.1:8500
```

## Verification URLs

See: [Ports and URLs](../reference/ports.md).

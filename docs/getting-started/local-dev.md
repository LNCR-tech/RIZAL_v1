# Getting Started (Local Dev, no Docker)

[<- Back to docs index](../../README.md)

This runs each service directly on your machine (useful for debugging and faster iteration).

## Prerequisites

- Python (backend + assistant)
- PostgreSQL (for `fastapi_db` and `ai_assistant`)
- Node.js + npm (frontend)

## Steps (High Level)

1. Create `.env` from `.env.example` and set DB URLs for your local Postgres (see [Environment Variables](../reference/env.md)).
2. Run backend migrations + seed, then start the API.
3. Start the assistant service.
4. Start the frontend dev server.

The canonical command list is here: [Common Commands](../reference/common-commands.md).

## Verification URLs

See: [Ports and URLs](../reference/ports.md).


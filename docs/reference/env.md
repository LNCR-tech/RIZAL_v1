# Environment Variables

[<- Back to docs index](../../README.md)

## Source of Truth

- Use `.env.example` as the authoritative list of supported keys and defaults.
- Backend settings are parsed in `Backend/app/core/config.py`.
- Frontend runtime configuration is injected via `Frontend/runtime-config.js.template` and Docker/NGINX templates.

## Minimum Local Setup (Docker)

Copy `.env.example` to `.env` and set at least:

- `SECRET_KEY`
- `JWT_SECRET`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- Assistant / AI:
  - `AI_MODEL`
  - `AI_API_BASE` (if not using default)
  - `AI_API_KEY`

Then run the Docker stack. See: [Getting Started (Docker)](../getting-started/docker.md).

## Minimum Local Setup (No Docker)

When running services manually, you will also need DB connection strings (see `.env.example` "MANUAL SETUP" section), notably:

- `DATABASE_URL`
- `DATABASE_ADMIN_URL`
- `ASSISTANT_DB_URL`
- `TENANT_DATABASE_URL`
- `APP_DATABASE_URL`

See: [Getting Started (Local Dev)](../getting-started/local-dev.md).



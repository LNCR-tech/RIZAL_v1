# Environment Variables

<!--nav-->
[← Common Commands](common-commands.md) | [🏠 Home](/README.md) | [Ports and URLs →](ports.md)

---
<!--/nav-->

## Separation Of Concerns

Use the env file that matches the process you are starting:

- Root `.env`
  Used by backend, assistant, Celery worker/beat, and repo-root `docker compose`.
- `frontend/.env.development.local`
  Used by frontend Vite dev when you run `npm run dev`.
- `frontend/.env.docker`
  Used only by the standalone frontend Docker setup inside `frontend/`.

Do not put frontend `VITE_*` local-dev overrides in the root `.env`.

Frontend-specific required vs optional variables are documented in:

- [Frontend configuration](../frontend/configuration.md)

## Local Setup

### Variables That Apply To Both Manual And Docker

Required in root `.env`:

- `SECRET_KEY`
- `AI_API_KEY`
- `AI_API_BASE`
- `AI_MODEL`

Optional in root `.env`:

- `JWT_ALGORITHM`
- `JWT_PUBLIC_KEY`
- `AI_PROVIDER` (optional; defaults to `openai` / OpenAI-compatible)
- `AI_MAX_TOKENS` (optional; must be <= the model's output token limit)
- `AI_API_VERSION` (optional; mainly for Anthropic/Gemini)
- email transport settings

Conditional email rules:

- if `EMAIL_TRANSPORT=disabled`, email credentials stay optional
- if `EMAIL_TRANSPORT=smtp`, `EMAIL_SENDER_EMAIL`, `EMAIL_SENDER_NAME`, and `SMTP_HOST` are required
- if `EMAIL_TRANSPORT=mailjet_api`, `EMAIL_SENDER_EMAIL`, `EMAIL_SENDER_NAME`, `MAILJET_API_KEY`, and `MAILJET_API_SECRET` are required

### Manual

Required in root `.env`:

- `DATABASE_URL`
- `ASSISTANT_DB_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `BACKEND_API_BASE_URL=http://127.0.0.1:8000`

Optional in root `.env`:

- `ASSISTANT_AUTO_MIGRATE`
- `LOGIN_URL`
- `CORS_ALLOWED_ORIGINS`
- `UVICORN_WORKERS`
- SMTP auth/TLS settings

Frontend local-dev variables:

- see [Frontend configuration](../frontend/configuration.md)

### Docker

Required in root `.env`:

- none beyond the shared local values for the current repo-root Docker flow

Optional in root `.env`:

- `FRONTEND_PORT`
- `EMAIL_TRANSPORT`
- `SMTP_*`
- `UVICORN_WORKERS`

Important:

- the repo-root `docker-compose.yml` hardcodes local container URLs for Postgres, Redis, backend, and assistant
- migrations and bootstrap run automatically on every `docker compose up --build` via the `migrate` and `bootstrap` services

## Production Setup

### Variables That Apply To Both Manual And Docker

Required:

- `SECRET_KEY`
- `AI_API_KEY`
- `AI_API_BASE`
- `AI_MODEL`

Optional:

- `JWT_ALGORITHM`
- `JWT_PUBLIC_KEY`
- email transport and sender settings

Conditional email rules:

- if `EMAIL_TRANSPORT=disabled`, email credentials stay optional
- if `EMAIL_TRANSPORT=smtp`, `EMAIL_SENDER_EMAIL`, `EMAIL_SENDER_NAME`, and `SMTP_HOST` are required
- if `EMAIL_TRANSPORT=mailjet_api`, `EMAIL_SENDER_EMAIL`, `EMAIL_SENDER_NAME`, `MAILJET_API_KEY`, and `MAILJET_API_SECRET` are required

### Manual

Required:

- production `DATABASE_URL`
- production `ASSISTANT_DB_URL`
- production `CELERY_BROKER_URL`
- production `CELERY_RESULT_BACKEND`
- production `BACKEND_API_BASE_URL`

Optional:

- `ASSISTANT_AUTO_MIGRATE`
- `LOGIN_URL`
- `CORS_ALLOWED_ORIGINS`
- `UVICORN_WORKERS`
- SMTP auth/TLS settings

### Docker

Required — change these from local defaults for production:

- `SECRET_KEY`
- `LOGIN_URL`
- `CORS_ALLOWED_ORIGINS`
- `BACKEND_ORIGIN`
- `ASSISTANT_ORIGIN`
- `BACKEND_API_BASE_URL`
- `DATABASE_URL` (if using external Postgres)
- `ASSISTANT_DB_URL` (if using external Postgres)

Optional:

- `FRONTEND_PORT` — change to `80` or `443`
- `EMAIL_TRANSPORT` — set to `mailjet_api`
- `MAILJET_API_KEY` — your Mailjet API key
- `MAILJET_API_SECRET` — your Mailjet API secret
- `SMTP_*` / `MAILJET_*`
- `UVICORN_WORKERS` — increase for production

Important:

- for external Postgres or Redis, update the hardcoded container URLs in `docker-compose.yml` or use a Compose override

## Source Of Truth

- Backend env parsing: `backend/app/core/config.py`
- Assistant DB/auth/env loading: `assistant/lib/database.py`, `assistant/lib/auth.py`, `assistant/lib/llm.py`
- Backend non-secret defaults: `backend/app/core/app_settings.py`
- Assistant non-secret defaults: `assistant/lib/app_settings.py`
- Frontend dev env loading: `frontend/vite.config.js`
- Frontend runtime env rendering: `frontend/runtime-config.js.template`

## Bootstrap

When running via Docker, bootstrap runs automatically as part of `docker compose up --build`.

For manual setup, run it explicitly:

```powershell
cd backend
python bootstrap.py
```

Or with custom credentials:

```powershell
python bootstrap.py --admin-email admin@example.com --admin-password ChangeMe123!
```

Default credentials are configured in `backend/app/core/app_settings.py`.

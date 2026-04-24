# Environment Variables

[<- Back to docs index](../../README.md)

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

- the current repo-root `docker-compose.yml` hardcodes local container URLs for Postgres, Redis, backend, and assistant
- root `.env` does not override those infrastructure URLs in the current Compose file

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

Required:

- no additional root `.env` variables are honored for external infra in the current repo-root Compose file because service URLs are hardcoded there

Optional:

- `FRONTEND_PORT`
- `EMAIL_TRANSPORT`
- `SMTP_*`
- `UVICORN_WORKERS`

Important:

- for a real production Docker deployment against external Postgres, Redis, backend, or assistant URLs, update `docker-compose.yml` or use a deployment-specific Compose override

## Source Of Truth

- Backend env parsing: `backend/app/core/config.py`
- Assistant DB/auth/env loading: `assistant-v2/lib/database.py`, `assistant-v2/lib/auth.py`, `assistant-v2/lib/llm.py`
- Backend non-secret defaults: `backend/app/core/app_settings.py`
- Assistant non-secret defaults: `assistant-v2/lib/app_settings.py`
- Frontend dev env loading: `frontend/vite.config.js`
- Frontend runtime env rendering: `frontend/runtime-config.js.template`

## Bootstrap

Initial admin creation is explicit and not driven by env toggles:

```powershell
python backend/bootstrap.py --admin-email admin@example.com --admin-password ChangeMe123!
```

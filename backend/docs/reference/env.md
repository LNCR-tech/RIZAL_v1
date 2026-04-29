# Environment Variables

<!--nav-->
[Previous](common-commands.md) | [Next](ports.md) | [Home](/README.md)

---
<!--/nav-->

## Separation Of Concerns

Use the env file that matches the process you are starting:

- Each service has its own `.env.example` — copy it to `.env` and fill in the values.
- `frontend-web/.env.development.local` — used by Vite dev when you run `npm run dev` inside `frontend-web/`.

Do not put frontend `VITE_*` local-dev overrides in any other service's `.env`.

Frontend-specific variables are documented in:

- [Frontend README](../../../frontend-web/README.md)

## Local Setup

### Variables That Apply To Both Manual And Docker

Required in `backend/.env`:

- `SECRET_KEY`
- `DATABASE_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

Required in `assistant/.env`:

- `AI_API_KEY`
- `AI_API_BASE`
- `AI_MODEL`
- `SECRET_KEY` (must match `backend/.env`)
- `ASSISTANT_DB_URL`
- `BACKEND_API_BASE_URL`

Optional:

- `JWT_ALGORITHM`
- `JWT_PUBLIC_KEY`
- `AI_MAX_TOKENS`
- email transport settings

Conditional email rules:

- if `EMAIL_TRANSPORT=disabled`, email credentials stay optional
- if `EMAIL_TRANSPORT=smtp`, `EMAIL_SENDER_EMAIL`, `EMAIL_SENDER_NAME`, and `SMTP_HOST` are required
- if `EMAIL_TRANSPORT=mailjet_api`, `EMAIL_SENDER_EMAIL`, `EMAIL_SENDER_NAME`, `MAILJET_API_KEY`, and `MAILJET_API_SECRET` are required

### Manual

Required in `backend/.env`:

- `DATABASE_URL=postgresql://postgres:<password>@127.0.0.1:5432/fastapi_db`
- `CELERY_BROKER_URL=redis://127.0.0.1:6379/0`
- `CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0`
- `LOGIN_URL=http://localhost:5173`
- `CORS_ALLOWED_ORIGINS=http://localhost:5173`

Required in `assistant/.env`:

- `ASSISTANT_DB_URL=postgresql://postgres:<password>@127.0.0.1:5432/ai_assistant`
- `BACKEND_API_BASE_URL=http://127.0.0.1:8000`

Optional:

- `ASSISTANT_AUTO_MIGRATE`
- `UVICORN_WORKERS`
- SMTP auth/TLS settings

Frontend local-dev variables:

- see [Frontend README](../../../frontend-web/README.md)

### Docker

Required — none beyond the per-service `.env` values above. The root `docker-compose.yml` hardcodes container-internal URLs for Postgres, Redis, backend, and assistant.

Optional:

- `FRONTEND_PORT`
- `EMAIL_TRANSPORT`
- `SMTP_*`
- `UVICORN_WORKERS`

Important:

- migrations and bootstrap run automatically on every `docker compose up --build` via the `migrate` and `bootstrap` services

## Production Setup

### Variables That Apply To Both Manual And Docker

Required:

- `SECRET_KEY` — use a long random string
- `AI_API_KEY`, `AI_API_BASE`, `AI_MODEL`

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
- `BACKEND_API_BASE_URL`
- `ASSISTANT_ORIGIN`
- `DATABASE_URL` (if using external Postgres)
- `ASSISTANT_DB_URL` (if using external Postgres)

Optional:

- `FRONTEND_PORT` — change to `80` or `443`
- `EMAIL_TRANSPORT` — set to `mailjet_api`
- `MAILJET_API_KEY`
- `MAILJET_API_SECRET`
- `SMTP_*` / `MAILJET_*`
- `UVICORN_WORKERS` — increase for production

Important:

- for external Postgres or Redis, update the hardcoded container URLs in `docker-compose.yml` or use a Compose override

## Source Of Truth

- Backend env parsing: `backend/app/core/config.py`
- Assistant DB/auth/env loading: `assistant/lib/database.py`, `assistant/lib/auth.py`, `assistant/lib/llm.py`
- Backend non-secret defaults: `backend/app/core/app_settings.py`
- Assistant non-secret defaults: `assistant/lib/app_settings.py`
- Frontend dev env loading: `frontend-web/vite.config.js`
- Frontend runtime env rendering: `frontend-web/runtime-config.js.template`

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

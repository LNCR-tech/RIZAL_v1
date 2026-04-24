# Environment Variables

[<- Back to docs index](../../README.md)

## Source of Truth

- `.env.example` now documents only secrets, connection strings, deployment URLs, and a few operational overrides.
- Backend non-secret defaults now live in `backend/app/core/app_settings.py`.
- Assistant non-secret defaults now live in `assistant-v2/lib/app_settings.py`.
- Backend env parsing remains in `backend/app/core/config.py`.
- Frontend runtime configuration is injected via `frontend/runtime-config.js.template` and the Docker/NGINX templates.

`.env.example` is no longer the source of truth for import limits, email timeouts, face thresholds, school-logo limits, or assistant model defaults.

## Minimum Docker Setup

Copy `.env.example` to `.env` and set at least:

- `SECRET_KEY`
- `DATABASE_URL` when you are not using the local Docker Postgres defaults
- `ASSISTANT_DB_URL` when you are not using the local Docker Postgres defaults
- `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` when you are not using the local Docker Redis defaults
- `AI_API_KEY`
- `AI_API_BASE` when you are using a non-default provider endpoint

Optional:

- SMTP settings when `EMAIL_TRANSPORT=smtp`:
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USE_TLS`
  - `SMTP_USE_STARTTLS`
  - `SMTP_USERNAME` and `SMTP_PASSWORD` (only when auth is required)
- Mailjet credentials when `EMAIL_TRANSPORT=mailjet_api`

## Minimum Manual Local Setup

When running services directly on your machine, set:

- `SECRET_KEY`
- `DATABASE_URL`
- `ASSISTANT_DB_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `AI_API_KEY`
- `BACKEND_API_BASE_URL=http://127.0.0.1:8000`

## Bootstrap

Initial production data is no longer configured through env toggles.

Use the explicit bootstrap command instead:

- `python backend/bootstrap.py --admin-email ... --admin-password ...`

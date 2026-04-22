[<- Back to docs index](../../README.md)

# Backend Railway / Constrained Deployment Guide

The repository now keeps a single compose file (`docker-compose.yml`). This page documents the constrained-platform variant for services such as Railway where you may still need a single backend container to host the web process plus optional worker sidecars.

## Current Runtime Behavior

`Backend/scripts/run_runtime_stack.py` now:

1. creates import and school-logo storage directories from `Backend/app/core/config.py`
2. optionally runs `alembic upgrade heads` when `RUN_MIGRATIONS_ON_START=true`
3. optionally launches Celery worker and beat sidecars
4. starts `uvicorn`

Important change:

- automatic demo seeding is no longer supported in the runtime stack
- `RUN_SEED_ON_START` is obsolete
- production bootstrap must be run explicitly with `python Backend/bootstrap.py ...`

## Recommended Platform Variables

- `DATABASE_URL=<managed postgres url>`
- `CELERY_BROKER_URL=<managed redis url>`
- `CELERY_RESULT_BACKEND=<managed redis url>`
- `SECRET_KEY=<strong secret>`
- `LOGIN_URL=<public frontend url>`
- `CORS_ALLOWED_ORIGINS=<public frontend origins>`
- `EMAIL_TRANSPORT=disabled` or `mailjet_api`
- `MAILJET_API_KEY=<mailjet key>` when email is enabled
- `MAILJET_API_SECRET=<mailjet secret>` when email is enabled
- `UVICORN_WORKERS=1`
- `CELERY_WORKER_POOL=solo`
- `CELERY_WORKER_CONCURRENCY=1`

Non-secret runtime defaults such as face warm-up and import limits now come from `Backend/app/core/app_settings.py`.

## Suggested Release Flow

1. Run migrations:
   - `alembic upgrade heads`
2. Run the one-time bootstrap:
   - `python Backend/bootstrap.py --admin-email admin@example.com --admin-password ChangeMe123!`
3. Start the web process.
4. Start worker and beat as separate processes or sidecars if the platform allows it.

## How to Test

1. Deploy with `EMAIL_TRANSPORT=disabled`.
2. Confirm startup logs show the API booted without trying to auto-seed.
3. Run the bootstrap command once.
4. Verify the admin can log in.
5. If Mailjet is enabled, run:
   - `python Backend/scripts/send_test_email.py --recipient <test inbox> --check-only`

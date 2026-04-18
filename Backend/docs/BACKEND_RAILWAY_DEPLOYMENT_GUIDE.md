# Backend Railway Deployment Guide

This guide documents the Railway-oriented backend runtime used by this repository.

## Service Layout

For small Railway plans, the backend can run in a single service with:

- API web server
- Celery worker
- Celery beat
- startup migrations
- startup seeding

This is controlled by these environment variables:

- `SERVICE_MODE=web`
- `RUN_MIGRATIONS_ON_START=true`
- `RUN_SEED_ON_START=true`
- `RUN_CELERY_WORKER=true`
- `RUN_CELERY_BEAT=true`
- `CELERY_WORKER_POOL=solo`
- `CELERY_WORKER_CONCURRENCY=1`
- `FACE_WARMUP_ON_STARTUP=false`

## Startup Behavior

When `SERVICE_MODE=web`, the backend now:

1. creates storage directories
2. runs `alembic upgrade heads` when `RUN_MIGRATIONS_ON_START=true`
3. runs `python seed.py` when `RUN_SEED_ON_START=true`
4. starts optional Celery worker and beat sidecars
5. starts `uvicorn`

`alembic upgrade heads` is required because the repository currently has multiple Alembic heads.

Face-runtime note:

- InsightFace startup now requests only the `detection` and `recognition` modules when constructing `FaceAnalysis(...)` to reduce model-load memory pressure.
- If your Railway service still restarts while face runtime initializes, keep `FACE_WARMUP_ON_STARTUP=false` and treat face-runtime readiness as a deployment-capacity issue (memory/plan sizing) before enabling startup warm-up.

## Recommended Railway Variables

- `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- `DATABASE_ADMIN_URL=${{Postgres.DATABASE_URL}}`
- `CELERY_BROKER_URL=${{Redis.REDIS_URL}}`
- `CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}`
- `UVICORN_WORKERS=1`
- `CELERY_WORKER_POOL=solo`
- `CELERY_WORKER_CONCURRENCY=1`
- `FACE_WARMUP_ON_STARTUP=false`
- `EMAIL_REQUIRED_ON_STARTUP=true`
- `EMAIL_VERIFY_CONNECTION_ON_STARTUP=true`

## How To Test

1. Deploy the backend service on Railway.
2. Confirm startup logs show:
   - migrations completed
   - seeding completed
   - Celery worker launch
   - Celery beat launch
   - `uvicorn` launch
   - when face init is enabled, InsightFace initialization logs show `allowed_modules=detection,recognition`
3. Verify the seeded admin can log in.
4. Run a backend email smoke test after deployment and confirm Gmail accepts the message.

# Environment Variables

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Source of truth:**
> - `Backend/app/core/config.py`
> - `docker-compose.yml`
> - `docker-compose.prod.yml`
> - `Frontend/src/api/apiUrl.ts`
> - `Frontend/vite.config.ts`

---

## Purpose

This page documents the runtime variables used by deployment, backend services, background jobs, and the frontend build or proxy flow.

## Safe Configuration Rules

- Never commit real secrets into documentation, compose files, or tracked `.env` files.
- Use placeholders such as `<db_password>` or `<long-random-secret>` in all examples.
- Keep development and production values separate.
- Treat `SECRET_KEY`, SMTP credentials, and database credentials as sensitive.

## Environment File Locations

| Location | Used by | Notes |
|---|---|---|
| Repo-root `.env` | `docker-compose.prod.yml` | Required for the production-style compose flow. |
| `Backend/.env` | `Backend/app/core/config.py` when the backend runs directly | Useful for local direct backend execution outside compose. |
| Frontend shell or `.env.local` style envs | Vite and frontend build | Used for `VITE_*` variables during frontend development or build. |

## Minimum Required Production Variables

These values should be explicitly set before any production-style deployment:

| Variable | Why it is required |
|---|---|
| `POSTGRES_USER` | Initializes and authenticates production Postgres user. |
| `POSTGRES_PASSWORD` | Secures production Postgres authentication. |
| `POSTGRES_DB` | Defines production database name. |
| `DATABASE_URL` | Backend primary DB connection string. |
| `SECRET_KEY` | JWT signing secret for auth integrity. |
| `CELERY_BROKER_URL` | Required broker path for worker and beat task routing. |
| `CELERY_RESULT_BACKEND` | Required async result backend for Celery task state. |
| `CORS_ALLOWED_ORIGINS` | Prevents unsafe cross-origin API usage. |
| `LOGIN_URL` | Used in auth and notification flows. |
| `VITE_API_URL` | Ensures frontend points to the expected API route. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS` | Required for stable email-based auth and notifications. |

## Core Backend Application Variables

| Variable | Example or default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql://<db_user>:<db_password>@db:5432/<db_name>` | Primary database connection string. Required in production. |
| `SECRET_KEY` | `<long-random-secret>` | JWT signing secret. Required in production. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime in minutes. |
| `CORS_ALLOWED_ORIGINS` | `https://<your-domain>` | Comma-separated allowed origins. |
| `LOGIN_URL` | `https://<your-domain>` or `http://localhost:5173` | Used in auth and notification flows. |

## Database and Performance Tuning

| Variable | Default | Notes |
|---|---|---|
| `DB_POOL_SIZE` | `10` | Base SQLAlchemy pool size. |
| `DB_MAX_OVERFLOW` | `10` | Extra connections beyond pool size. |
| `DB_POOL_TIMEOUT_SECONDS` | `15` | Wait time when the pool is exhausted. |
| `DB_POOL_RECYCLE_SECONDS` | `1800` | Connection recycle interval. |
| `UVICORN_WORKERS` | `2` | Used by the production backend container startup command. |

## Face Recognition and Attendance Controls

| Variable | Default | Notes |
|---|---|---|
| `FACE_MATCH_THRESHOLD` | `0.5` | Match threshold for face comparison. |
| `LIVENESS_MIN_SCORE` | `0.85` | Minimum score for liveness checks. |
| `ALLOW_LIVENESS_BYPASS_WHEN_MODEL_MISSING` | `false` | Development-only fallback if the liveness model is missing. |
| `ANTI_SPOOF_SCALE` | `2.7` | Anti-spoof image scaling factor. |
| `ANTI_SPOOF_MODEL_PATH` | empty | Optional explicit model path. |
| `GEO_MAX_ALLOWED_ACCURACY_M` | `30` | Maximum accepted GPS accuracy in meters. |
| `GEO_MAX_TRAVEL_SPEED_MPS` | `60` | Travel-speed validation threshold. |
| `PUBLIC_ATTENDANCE_ENABLED` | `true` | Code-level flag for the public face-scan flow. |
| `PUBLIC_ATTENDANCE_MAX_FACES_PER_FRAME` | `10` | Max faces processed per frame. |
| `PUBLIC_ATTENDANCE_SCAN_COOLDOWN_SECONDS` | `8` | Cooldown between scans. |
| `PUBLIC_ATTENDANCE_EVENT_LOOKAHEAD_HOURS` | `12` | Event lookahead window for public attendance scanning. |

## Import and Background Job Controls

| Variable | Default | Notes |
|---|---|---|
| `IMPORT_MAX_FILE_SIZE_MB` | `50` | Upload limit for import files. |
| `IMPORT_CHUNK_SIZE` | `5000` | Row batch size during import processing. |
| `IMPORT_STORAGE_DIR` | `/tmp/valid8_imports` | Shared import storage path. |
| `IMPORT_RATE_LIMIT_COUNT` | `3` | Allowed import attempts within the rate-limit window. |
| `IMPORT_RATE_LIMIT_WINDOW_SECONDS` | `300` | Import rate-limit window length. |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Active Celery broker URL. |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Celery result backend URL. |
| `CELERY_TASK_TIME_LIMIT_SECONDS` | `10800` | Hard limit for long-running tasks. |
| `REDIS_URL` | `redis://redis:6379/0` | Fallback base used when explicit Celery URLs are not provided. |
| `EVENT_STATUS_SYNC_ENABLED` | `true` | Enables scheduled event status sync. |
| `EVENT_STATUS_SYNC_INTERVAL_SECONDS` | `60` | Interval for the beat-driven event sync. |

## Email, Storage, and Branding Variables

| Variable | Example or default | Notes |
|---|---|---|
| `SMTP_HOST` | `<smtp-host>` | SMTP server host. |
| `SMTP_PORT` | `587` | SMTP server port. |
| `SMTP_USERNAME` | `<smtp-username>` | SMTP username. Sensitive. |
| `SMTP_PASSWORD` | `<smtp-password>` | SMTP password. Sensitive. |
| `SMTP_FROM_EMAIL` | `noreply@<your-domain>` | Sender address for email flows. |
| `SMTP_USE_TLS` | `true` | Enables TLS for SMTP connections. |
| `SCHOOL_LOGO_STORAGE_DIR` | `/tmp/valid8_school_logos` | Shared storage path for uploaded logos. |
| `SCHOOL_LOGO_MAX_FILE_SIZE_MB` | `2` | Max logo upload size. |
| `SCHOOL_LOGO_PUBLIC_PREFIX` | `/media/school-logos` | Public URL prefix used by the backend. |

## Compose and Frontend Variables

| Variable | Example or default | Notes |
|---|---|---|
| `POSTGRES_USER` | `<db_user>` | Used by the production PostgreSQL container. |
| `POSTGRES_PASSWORD` | `<db_password>` | Used by the production PostgreSQL container. Sensitive. |
| `POSTGRES_DB` | `<db_name>` | Used by the production PostgreSQL container. |
| `FRONTEND_PORT` | `80` | Host port for the production frontend container. |
| `VITE_API_URL` | `/api` for production, `http://localhost:8000` for direct local use | Frontend API base URL used at build time or in local env. |
| `VITE_DEV_PROXY_TARGET` | `http://backend:8000` | Vite development proxy target. |

## Safe Example for Production `.env`

```env
POSTGRES_USER=<db_user>
POSTGRES_PASSWORD=<db_password>
POSTGRES_DB=<db_name>
DATABASE_URL=postgresql://<db_user>:<db_password>@db:5432/<db_name>
SECRET_KEY=<long-random-secret>
CORS_ALLOWED_ORIGINS=https://<your-domain>
LOGIN_URL=https://<your-domain>
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
VITE_API_URL=/api
UVICORN_WORKERS=2
SMTP_HOST=<smtp-host>
SMTP_PORT=587
SMTP_USERNAME=<smtp-username>
SMTP_PASSWORD=<smtp-password>
SMTP_FROM_EMAIL=noreply@<your-domain>
SMTP_USE_TLS=true
```

## Sensitive Variable Handling

| Classification | Variables | Handling rule |
|---|---|---|
| Secret credentials | `POSTGRES_PASSWORD`, `SMTP_PASSWORD`, `SECRET_KEY` | Never commit. Store in deployment secret manager or protected environment. |
| Sensitive endpoints and auth context | `DATABASE_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CORS_ALLOWED_ORIGINS`, `LOGIN_URL` | Keep environment-specific and reviewed per release. |
| Operational but non-secret | `UVICORN_WORKERS`, `FRONTEND_PORT`, retention and tuning values | Track in deployment config, still review for environment fit. |

Redaction rule for documentation and logs:

- Show names and purpose only.
- Use placeholders for values.
- Never paste live credentials in Markdown, screenshots, issue comments, or CI logs.

## Documentation Controls

- Update this page whenever `Backend/app/core/config.py`, compose files, or frontend Vite settings change.
- If a variable is renamed in code, update the docs in the same change set.
- If a variable is sensitive, document only its purpose and a safe placeholder.

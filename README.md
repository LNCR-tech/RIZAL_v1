# sas-v1

Valid8 Attendance Recognition System (Dockerized full stack).

## Stack
- Backend: FastAPI, SQLAlchemy, Alembic, Celery, Celery Beat, Redis
- Frontend: Vue 3 + Vite + Tailwind (Capacitor-ready)
- Assistant: FastAPI (streaming SSE chat API, proxied by the frontend nginx at `/__assistant__/`)
- Database: PostgreSQL
- Tools: Docker Compose, pgAdmin

## Project Structure
- `Backend/` - FastAPI backend and workers
- `Frontend/` - Vue frontend for the monorepo stack
- root frontend files from `mr.frontend` - standalone/frontend-only Docker assets and alternate UI structure
- `Databse/` - project database-related assets
- `docker-compose.yml` - local multi-service orchestration

## Backend Documentation
- Main backend merge guide: `Backend/docs/BACKEND_FACE_GEO_MERGE_GUIDE.md`
- Backend change log: `Backend/docs/BACKEND_CHANGELOG.md`
- Attendance status guide: `Backend/docs/BACKEND_ATTENDANCE_STATUS_GUIDE.md`
- Event time status guide: `Backend/docs/BACKEND_EVENT_TIME_STATUS_GUIDE.md`
- Event auto status guide: `Backend/docs/BACKEND_EVENT_AUTO_STATUS_GUIDE.md`
- Google email delivery guide: `Backend/docs/BACKEND_GOOGLE_EMAIL_DELIVERY_GUIDE.md`

## Quick Start
1. Install Docker Desktop.
2. From project root, run:

### Windows (recommended)

This runs Docker in the background and prints the local URLs plus the seeded user credentials in the same terminal output.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-up.ps1
```

### Any OS

```bash
docker compose up -d --build
```

### Assistant LLM Key (Required For Real Replies)

The Assistant service will run without an LLM key, but it will respond with an "LLM is not configured" message until you provide one.

Option A, PowerShell (current session only):

```powershell
$env:LLM_API_KEY="your_key_here"
# Optional:
# $env:LLM_MODEL="gpt-4o-mini"
# $env:LLM_API_BASE="https://api.openai.com/v1"
docker compose up -d --build
```

Option B, repo-root `.env` file (picked up by Docker Compose automatically):

```env
LLM_API_KEY=your_key_here
# Optional:
# LLM_MODEL=gpt-4o-mini
# LLM_API_BASE=https://api.openai.com/v1
```

3. Open:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- pgAdmin: `http://localhost:5050`
- Assistant health (via frontend proxy): `http://localhost:5173/__assistant__/health`

To print the seeded demo credentials (the `seed` one-shot container logs):

```bash
docker compose logs --no-color --tail=200 seed
```

If you're on Windows and want the URLs + credentials printed in a nicer format:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-info.ps1
```

## Automated Testing

Backend tests (pytest) run in Docker and use in-memory SQLite fixtures (no DB/Redis needed):

```bash
docker compose run --rm test_backend
```

Windows convenience wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test-backend.ps1
```

API-based tester suites (simulated user actions; writes PSV logs under `./cmpj/`):

```powershell
docker compose --profile test run --rm auto_tests
```

Windows one-liner wrapper (brings stack up without rebuild, then runs suites):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-auto-tests.ps1
```

## Frontend-Only Docker Notes

The root-level files added from `mr.frontend` include a standalone frontend Docker path:
- `Dockerfile`
- `nginx.conf.template`
- `runtime-config.js.template`
- `.env.docker.example`
- `docker-entrypoint.d/40-runtime-config.sh`

These can be used for frontend-only/demo container workflows, but the primary project orchestration for this repository remains the root `docker-compose.yml` full-stack setup above.

## Environment Notes
- Backend mail example values are in `Backend/.env.example`.
- Frontend API base URL can be configured via `Frontend/.env.*` (`VITE_API_BASE_URL`, `VITE_API_TIMEOUT_MS`) and runtime config (`AURA_API_BASE_URL`, `AURA_API_TIMEOUT_MS`).
- Assistant replies require an LLM key (set `LLM_API_KEY` or `OPENAI_API_KEY` for the assistant service in Compose).
- Compose defaults backend DB/Celery settings for local Docker networking.
- Event auto-status scheduler can be configured with `EVENT_STATUS_SYNC_ENABLED` and `EVENT_STATUS_SYNC_INTERVAL_SECONDS`.

# Aura — Student Attendance System

Aura is a school-grade student attendance management system with face recognition, QR/RFID scanning, geolocation check-in, governance hierarchy, sanctions, AI assistant, and reporting.

## Services

| Folder | Description |
|---|---|
| `backend/` | FastAPI API, Alembic migrations, Celery workers |
| `frontend-web/` | Vue 3 (Vite) SPA + Capacitor mobile |
| `frontend-apk/` | Capacitor Android native project |
| `assistant/` | Streaming LLM assistant with MCP tool integration |
| `database/` | Postgres service, schema docs, Docker init scripts |
| `seeder/` | Demo data seeder (dev only) |

## Quick Start

### Development

```powershell
# 1. Copy and configure each service's environment
Copy-Item backend\.env.example backend\.env
Copy-Item assistant\.env.example assistant\.env
Copy-Item database\.env.example database\.env
Copy-Item frontend-web\.env.example frontend-web\.env

# 2. Fill in the required values in each .env file

# 3. Start everything in dev mode (includes pgAdmin + Mailpit)
docker compose --profile dev up --build
```

When ready:

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- Assistant docs: `http://localhost:8500/docs`
- Mailpit (email capture): `http://localhost:8025`
- pgAdmin: `http://localhost:5050`
- Log viewer: `http://localhost:8080`

### Production

```powershell
docker compose --profile prod up --build
```

Production excludes pgAdmin and Mailpit. Make sure to set production values in each `.env` before deploying — see `SECURITY.md`.

## Database Seeding (Dev Only)

To populate the database with demo data:

```powershell
# In seeder/.env, set:
# SEED_DATABASE=true
# SEED_CONFIRM=yes
# SEED_WIPE_EXISTING=true

cd seeder
python seed.py demo
```

Or via Docker — the seeder service runs automatically if `SEED_DATABASE=true` and `SEED_CONFIRM=yes` are set in your `.env`.

## Environment Variables

Each service has its own `.env.example`. Copy it to `.env` and fill in the values.

Variables are tagged with one of four types:

- `[BEHAVIOR]` — controls how this service behaves. Independent — nothing else depends on this value.
- `[IDENTITY]` — credentials or secrets that define who this service is. Independent — you choose them, but other services may need to copy them into their own `[NEIGHBOR]` variables.
- `[ENDPOINT]` — this service's own address or port that other services connect to. You choose the value, but other services must match it.
- `[NEIGHBOR]` — URL or address of another service this service talks to. Dependent — must match the target service's `[ENDPOINT]` or `[IDENTITY]`.

## Documentation

- [Security Guide](SECURITY.md)
- [Backend docs](backend/docs/)
- [Frontend docs](frontend-web/docs/)
- [Assistant docs](assistant/docs/)
- [Database docs](database/)
- [Seeder docs](seeder/docs/)
- [Audit Report](frontend-web/docs/audits/AUDIT_REPORT.md)

## README Index

- [Assistant README](assistant/README.md)
- [Backend README](backend/README.md)
- [Database README](database/README.md)
- [Frontend README](frontend-web/README.md)
- [Frontend APK README](frontend-apk/README.md)
- [Seeder README](seeder/README.md)

## Notes

- Redis/Celery is required for background jobs (bulk import, email delivery).
- Non-secret backend defaults live in `backend/app/core/app_settings.py`.
- Non-secret assistant defaults live in `assistant/lib/app_settings.py`.
- Migrations run automatically on `docker compose up` via the `migrate` service.

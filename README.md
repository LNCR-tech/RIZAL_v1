# Aura (Student Attendance System)

This repo contains:
- `Backend/`: FastAPI API + Alembic migrations + Celery tasks
- `Assistant-v2/` & `Assistant-v1/`: FastAPI assistant services (MCP tools + chat endpoint) with Postgres-backed storage. Active development is in v2.
- `Frontend/`: Vue 3 (Vite) SPA

## Quick Start (Docker)

This is the fastest way to get the system running. It handles the database, migrations, and seeding automatically.

### 1) Prerequisites
- **Docker Desktop** installed and running.
- A valid `.env` file in the project root.

### 2) Core `.env` Checklist
Before starting, ensure these values in your `.env` are correct:
- **AI_API_KEY**: Set this to your OpenAI or SiliconFlow/DeepSeek key for the AI Assistant to work.
- **AI_MODEL**: The model name (e.g., `gpt-4o` or `deepseek-ai/DeepSeek-V3.2`).
- **ASSISTANT_VERSION**: Set to `v2` (default) or `v1`. This dynamically controls which assistant container builds.
- **ADMIN_EMAIL/PASSWORD**: These will be your login credentials for the first run.
- **SECRET_KEY**: Change this if you plan to deploy the site publicly.
- **EMAIL_TRANSPORT**: For local Docker runs, keep this `disabled` (default) unless you have explicitly configured `smtp` or `gmail_api`.

### 3) Run One-Line Command
Open your terminal in the project root and run:

```powershell
docker compose up --build
```

**What happens next?**
- All images will be built.
- The database will be created and migrated.
- Sample data (Users, Schools, Orgs) will be seeded.
- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **pgAdmin (DB GUI)**: [http://localhost:5050](http://localhost:5050) (Login: admin@example.com / admin123)
- **Mailpit (Email Test)**: [http://localhost:8025](http://localhost:8025)
- **Database Port**: `5433` (exposed for tools like DBeaver; internal Postgres is 5432)
- **AI Visuals**: Aura now supports native, full-screen data visualization (Bar, Pie, Doughnut).

Note: If you want to test outbound email locally with Mailpit, set the following in your root `.env`:

```ini
EMAIL_TRANSPORT=smtp
SMTP_HOST=mailpit
SMTP_PORT=1025
EMAIL_SENDER_EMAIL=notifications@example.com
```

---

## Manual Run (No Docker)

### Prereqs
- Python installed (and your environment has the packages from `Backend/requirements.txt` and `Assistant/requirements.txt`)
- PostgreSQL running locally
- Node.js + npm for the frontend

### 1) Create `.env`
Copy and edit the repo-root env file:

```powershell
cd C:\Users\cmpj\dev\work\Collab\aurav3
Copy-Item .\.env.example .\.env
notepad .\.env
```

Minimum working values (example):

```ini
DATABASE_URL=postgresql://postgres:<PASSWORD>@localhost:5432/fastapi_db
ASSISTANT_DB_URL=postgresql://postgres:<PASSWORD>@localhost:5432/ai_assistant
APP_DATABASE_URL=postgresql://postgres:<PASSWORD>@localhost:5432/fastapi_db
TENANT_DATABASE_URL=postgresql://postgres:<PASSWORD>@localhost:5432/fastapi_db

# Assistant AI config (OpenAI-compatible API)
AI_MODEL=deepseek-ai/DeepSeek-V3.2
AI_API_BASE=https://api.siliconflow.com/v1
AI_API_KEY=<YOUR_KEY>
AI_MAX_TOKENS=16384
AI_PROVIDER=openai # (Set to 'openai', 'anthropic', or 'gemini')
```

### 2) Create the databases
Create empty DBs in Postgres (pgAdmin or `psql`):

```sql
CREATE DATABASE fastapi_db;
CREATE DATABASE ai_assistant;
```

### 3) Apply backend schema (migrations)

```powershell
cd C:\Users\cmpj\dev\work\Collab\aurav3\Backend
python -m alembic upgrade head
python .\seed.py
```

### 4) Run the backend API

```powershell
cd C:\Users\cmpj\dev\work\Collab\aurav3\Backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify:
- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

### 5) Run the assistant
The assistant auto-loads `.env` from the repo root at startup.

```powershell
cd C:\Users\cmpj\dev\work\Collab\aurav3\Assistant-v2
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8500
```

Verify:
- `http://127.0.0.1:8500/health`
- `http://127.0.0.1:8500/docs`

### 6) Run the frontend

```powershell
cd C:\Users\cmpj\dev\work\Collab\aurav3\Frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`.

## Documentation Directory

For deep technical details, guides, and architecture comparisons, refer to the organized documentation:

### Backend
- [Backend Changelog](./docs/backend/BACKEND_CHANGELOG.md)
- [Reports Module Guide](./docs/backend/BACKEND_REPORTS_MODULE_GUIDE.md)
- [Report Catalog](./docs/backend/REPORT_CATALOG.md)
- [Sanctions Management](./docs/backend/BACKEND_SANCTIONS_MANAGEMENT_GUIDE.md)
- [User Preferences & Auth Session](./docs/backend/BACKEND_USER_PREFERENCES_AND_AUTH_SESSION_GUIDE.md)
- [Demo Seeding Guide](./docs/backend/BACKEND_DEMO_SEEDING_GUIDE.md)
- [Large Data Seed Guide](./docs/backend/BACKEND_LARGE_DATA_SEED_GUIDE.md)
- [Face Engine Migration Guide](./docs/backend/BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md)
- [Email Local Testing Guide](./docs/backend/BACKEND_EMAIL_LOCAL_TESTING_GUIDE.md)
- [Railway Deployment Guide](./docs/backend/BACKEND_RAILWAY_DEPLOYMENT_GUIDE.md)

### Assistant
#### [v2 (Active Development)]
- [v1 vs v2 Full Comparison](./docs/assistant-v2/v1_vs_v2_comparison.md)

#### [v1 (Legacy)]
- [Assistant API Contract](./docs/assistant-v1/ASSISTANT_API_CONTRACT.md)
- [Assistant DB Schema](./docs/assistant-v1/ASSISTANT_DB_SCHEMA.md)
- [Legacy MCP README](./docs/assistant-v1/mcp_readme.md)

### Audits
- [Root Audit Report](./docs/audits/AUDIT_REPORT.md)
- [Project Audit](./docs/audits/project_audit.md)

## Notes
- Redis/Celery: the API can start without Redis, but features that enqueue background jobs will not run until Redis + a Celery worker/beat are running.
- Alembic error `Can't locate revision identified by 'merge_heads_aur'`: your DB has a stale `alembic_version` value from another migration history. Drop/recreate the DB and re-run `alembic upgrade head`.

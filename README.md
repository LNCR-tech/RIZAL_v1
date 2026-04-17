# Aura (Student Attendance System)

This repo contains:
- `Backend/`: FastAPI API + Alembic migrations + Celery tasks
- `Assistant/`: FastAPI assistant service (MCP tools + chat endpoint) with Postgres-backed storage
- `Frontend/`: Vue 3 (Vite) SPA

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

# Assistant LLM config (OpenAI-compatible API)
LLM_MODEL=deepseek-ai/DeepSeek-V3.2
LLM_API_BASE=https://api.siliconflow.com/v1
LLM_API_KEY=<YOUR_KEY>
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
cd C:\Users\cmpj\dev\work\Collab\aurav3\Assistant
python -m uvicorn assistant:app --reload --host 127.0.0.1 --port 8501
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

## Notes
- Redis/Celery: the API can start without Redis, but features that enqueue background jobs will not run until Redis + a Celery worker/beat are running.
- Alembic error `Can't locate revision identified by 'merge_heads_aur'`: your DB has a stale `alembic_version` value from another migration history. Drop/recreate the DB and re-run `alembic upgrade head`.

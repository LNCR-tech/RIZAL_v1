# Getting Started (Local Dev, no Docker)

<!--nav-->
[← Docker](docker.md) | [🏠 Home](/README.md) | [Linux / AWS Deploy →](linux-deploy.md)

---
<!--/nav-->

This runs each service directly on your machine without Docker. Useful for faster iteration and debugging.

---

## Prerequisites

| Requirement | Version | Linux | Windows |
|---|---|---|---|
| Python | 3.11+ | `apt install python3` | [python.org](https://www.python.org/downloads/) |
| PostgreSQL | 14+ | `apt install postgresql` | [postgresql.org](https://www.postgresql.org/download/windows/) |
| Redis | 6+ | `apt install redis` | Run via WSL (see note below) |
| Node.js | 18+ | `apt install nodejs` | [nodejs.org](https://nodejs.org/) |
| npm | 9+ | Comes with Node.js | Comes with Node.js |

---

## 1. Create the Databases

Connect to your local Postgres and run:

```sql
CREATE DATABASE fastapi_db;
CREATE DATABASE ai_assistant;
```

**Linux:**
```bash
psql -U postgres -c "CREATE DATABASE fastapi_db;"
psql -U postgres -c "CREATE DATABASE ai_assistant;"
```

**Windows (PowerShell):**
```powershell
psql -U postgres -c "CREATE DATABASE fastapi_db;"
psql -U postgres -c "CREATE DATABASE ai_assistant;"
```

---

## 2. Configure Environment Files

**Root `.env`** — copy from example and fill in required values:

```bash
# Linux
cp .env.example .env

# Windows
Copy-Item .\.env.example .\.env -Force
```

Required values to set in `.env`:

```env
SECRET_KEY=any-local-dev-string
AI_API_KEY=your-api-key
AI_API_BASE=https://api.openai.com/v1
AI_MODEL=gpt-4o

DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/fastapi_db
ASSISTANT_DB_URL=postgresql://postgres:postgres@127.0.0.1:5432/ai_assistant
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
BACKEND_API_BASE_URL=http://127.0.0.1:8000
LOGIN_URL=http://localhost:5173
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

**Frontend** — copy from example:

```bash
# Linux
cp frontend/.env.development.local.example frontend/.env.development.local

# Windows
Copy-Item .\frontend\.env.development.local.example .\frontend\.env.development.local -Force
```

---

## 3. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Assistant:**
```bash
cd assistant-v2
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm ci
```

---

## 4. Run Migrations

```bash
cd backend
python -m alembic upgrade heads
```

---

## 5. Run Bootstrap

```bash
cd backend
python bootstrap.py
```

This creates the platform admin account, roles, and event types. Safe to run multiple times.

---

## 6. Start All Services

Open a separate terminal for each service. Start them in this order:

**Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Worker:**

```bash
# Linux
cd backend
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

```powershell
# Windows — requires --pool=solo, otherwise Celery crashes
cd backend
celery -A app.workers.celery_app.celery_app worker --loglevel=info --pool=solo
```

**Beat:**
```bash
cd backend
celery -A app.workers.celery_app.celery_app beat --loglevel=info
```

**Assistant:**
```bash
cd assistant-v2
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8500
```

**Frontend:**
```bash
cd frontend
npm run dev
```

---

## Service URLs

| Service | URL |
|---|---|
| Frontend | `http://localhost:5173` |
| Backend API docs | `http://localhost:8000/docs` |
| Assistant API docs | `http://localhost:8500/docs` |

---

## Default Credentials

| Role | Email | Password |
|---|---|---|
| Platform Admin | `admin@aura.com` | `AdminPass123!` |

---

## Redis on Windows

Redis does not have an official native Windows build. The recommended approach is to run it inside WSL:

```powershell
# Install WSL if not already installed
wsl --install

# Inside WSL
sudo apt update && sudo apt install redis -y
sudo service redis start
```

Then use the WSL IP in `.env` instead of `127.0.0.1`:

```env
CELERY_BROKER_URL=redis://<wsl-ip>:6379/0
CELERY_RESULT_BACKEND=redis://<wsl-ip>:6379/0
```

Get your WSL IP:
```powershell
wsl hostname -I
```

This IP changes on every reboot — update `.env` if Celery fails to connect.


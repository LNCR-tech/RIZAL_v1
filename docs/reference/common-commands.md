# Common Commands

[<- Back to docs index](../../README.md)

Quick reference for all common operations. All commands run from the repo root unless noted.

---

## Docker (Local)

Start everything:
```bash
docker compose up --build
```

Stop:
```bash
docker compose down
```

Stop and wipe all data (including database):
```bash
docker compose down -v
```

Follow logs:
```bash
docker compose logs -f
docker compose logs -f backend   # one service
```

---

## Production (Ubuntu / AWS)

Start / first-time setup:
```bash
./start.sh
```

Stop:
```bash
./start.sh stop
```

Pull latest and redeploy:
```bash
./start.sh update
```

Follow logs:
```bash
./start.sh logs
./start.sh logs backend
```

Check status:
```bash
./start.sh status
```

Wipe everything including database:
```bash
./start.sh reset
```

---

## Backend (Manual)

Run from `backend/`:

```bash
# Migrations
python -m alembic upgrade heads

# Bootstrap (first run, idempotent)
python bootstrap.py

# API server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Celery worker
celery -A app.workers.celery_app.celery_app worker --loglevel=info

# Celery beat
celery -A app.workers.celery_app.celery_app beat --loglevel=info
```

---

## Assistant (Manual)

Run from `assistant-v2/`:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8500
```

---

## Frontend (Manual)

Run from `frontend/`:

```bash
npm ci          # install dependencies
npm run dev     # start dev server
npm run build   # production build
```

---

## Seeder (Manual)

Run from `seeder/`:

```bash
python seed.py demo

# With overrides
python seed.py demo --schools 3 --min-students 500 --max-students 1000
python seed.py demo --credentials-format tsv
```

Seeder only runs if `SEED_DATABASE = True` in `seeder/variables.py`.

---

## Database (Manual)

Create databases (first time only):

```bash
psql -U postgres -c "CREATE DATABASE fastapi_db;"
psql -U postgres -c "CREATE DATABASE ai_assistant;"
```

---

## Git

```bash
git add -A
git commit -m "your message"
git pull --rebase origin integrate/pilot-merge
git push
```

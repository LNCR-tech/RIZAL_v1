# Common Commands

[<- Back to docs index](../../README.md)

All commands are meant to be run from the repo root unless noted.

## Docker (Local All-in-One)

```powershell
Copy-Item .\.env.example .\.env -Force
docker compose up --build
```

Stop:

```powershell
docker compose down
```

## Docker (Production-Style Flow)

Run migrations:

```powershell
docker compose up --build migrate
```

Bootstrap the first admin and school:

```powershell
docker compose run --rm backend python bootstrap.py --admin-email admin@example.com --admin-password ChangeMe123!
```

Start the long-running services:

```powershell
docker compose up -d backend worker beat assistant frontend
```

## Backend (Local)

```powershell
cd .\Backend
python -m alembic upgrade head
python .\bootstrap.py --admin-email admin@example.com --admin-password ChangeMe123!
python .\seed.py --schools 5 --users 100
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Assistant v2 (Local)

```powershell
cd .\Assistant-v2
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8500
```

## Frontend (Local)

```powershell
cd .\Frontend
npm ci
npm run dev
```

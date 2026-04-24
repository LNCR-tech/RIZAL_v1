# Common Commands

[<- Back to docs index](../../README.md)

All commands are meant to be run from the repo root unless noted.

## Docker

```powershell
Copy-Item .\.env.example .\.env -Force
docker compose up --build
```

Stop:

```powershell
docker compose down
```

## Backend (Local)

```powershell
cd .\backend
python -m alembic upgrade head
python .\bootstrap.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Assistant v2 (Local)

```powershell
cd .\assistant-v2
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8500
```

## Frontend (Local)

```powershell
cd .\frontend
npm ci
npm run dev
```

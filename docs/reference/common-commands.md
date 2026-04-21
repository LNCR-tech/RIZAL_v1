# Common Commands

[<- Back to docs index](../../README.md)

All commands are meant to be run from the repo root unless noted.

## Docker (All-in-One)

```powershell
Copy-Item .\\.env.example .\\.env -Force
docker compose up --build
```

Assistant docs in Docker are reachable via the frontend proxy: `http://localhost:5173/__assistant__/docs`.

Stop:

```powershell
docker compose down
```

## Backend (Local)

```powershell
cd .\\Backend
python -m alembic upgrade head
python .\\seed.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Assistant v2 (Local)

```powershell
cd .\\Assistant-v2
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8500
```

## Frontend (Local)

```powershell
cd .\\Frontend
npm ci
npm run dev
```


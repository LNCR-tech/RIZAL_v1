# sas-v1

Valid8 Attendance Recognition System (Dockerized full stack).

## Stack
- Backend: FastAPI, SQLAlchemy, Alembic, Celery, Redis
- Frontend: React + TypeScript + Vite
- Database: PostgreSQL
- Tools: Docker Compose, pgAdmin

## Project Structure
- `Backend/` - FastAPI backend and workers
- `Frontend/` - React frontend
- `Databse/` - project database-related assets
- `docker-compose.yml` - local multi-service orchestration

## Quick Start
1. Install Docker Desktop.
2. From project root, run:

```bash
docker compose up --build
```

3. Open:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- pgAdmin: `http://localhost:5050`

## Environment Notes
- SMTP example values are in `.env.smtp.example`.
- Frontend API URL is configured in `Frontend/.env` (`VITE_API_URL`).
- Compose defaults backend DB/Celery settings for local Docker networking.

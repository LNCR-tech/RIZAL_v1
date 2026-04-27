# Backend Service

FastAPI backend for Aura. Handles authentication, attendance, events, governance, sanctions, reports, bulk import, and face recognition.

## Stack

- Python + FastAPI
- SQLAlchemy ORM + Alembic migrations
- Celery + Redis for background jobs
- bcrypt, JWT, InsightFace, ONNX

## Setup

```bash
cd backend
cp .env.example .env
# fill in all values

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Docs

- [Backend Docs](docs/README.md)
- API docs: `http://localhost:8000/docs` (dev only, disabled in production)

## Key Directories

- `app/models/` — SQLAlchemy models
- `app/routers/` — API route handlers
- `app/services/` — business logic
- `app/schemas/` — Pydantic request/response schemas
- `alembic/` — database migrations
- `tests/` — pytest test suite

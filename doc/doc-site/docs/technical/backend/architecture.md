---
sidebar_position: 1
title: Architecture
---

# Backend Architecture

🔒 **Restricted**: Developer documentation

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 + pgvector
- **Cache**: Redis
- **Task Queue**: Celery + Redis
- **Face Recognition**: InsightFace (ONNX)
- **Migrations**: Alembic

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Config, security, deps
│   ├── db/               # Database models
│   ├── services/         # Business logic
│   ├── schemas/          # Pydantic models
│   └── utils/            # Helpers
├── alembic/              # Migrations
├── tests/                # Test suite
└── main.py               # Entry point
```

## Key Components

### 1. API Layer (`app/api/`)
RESTful endpoints organized by domain:
- `auth.py` — Authentication
- `users.py` — User management
- `events.py` — Event CRUD
- `attendance.py` — Check-in/out
- `face.py` — Face recognition

### 2. Service Layer (`app/services/`)
Business logic separated from routes:
- `auth_service.py`
- `face_service.py`
- `attendance_service.py`
- `notification_service.py`
- `sanction_service.py`

### 3. Database Layer (`app/db/`)
SQLAlchemy models with normalized schema.

### 4. Background Tasks (`app/tasks/`)
Celery workers for:
- Bulk student import
- Email delivery
- Report generation
- Face embedding computation

## Request Flow

```
Client → FastAPI Route → Service Layer → Database
                      ↓
                   Celery Task (async)
```

## Security

- JWT-based authentication
- Role-based access control (RBAC)
- Password hashing (bcrypt)
- CORS configuration
- Rate limiting

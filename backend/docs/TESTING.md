# Backend Testing Guide

## Overview

The backend has a pytest suite covering 18 of 20 routers — 67 tests total. Tests run against a real PostgreSQL database using the same schema as production.

## Running Tests Locally

```powershell
cd backend
pytest
```

Verbose output:

```powershell
pytest -v
```

Run a specific file:

```powershell
pytest tests/test_auth.py -v
```

### Prerequisites

- PostgreSQL running locally with `fastapi_db` database created
- All migrations applied: `alembic upgrade heads`
- `backend/.env` with at minimum:

```env
DATABASE_URL=postgresql://postgres:<password>@127.0.0.1:5432/fastapi_db
SECRET_KEY=any-string-for-local-testing
RATE_LIMIT_ENABLED=false
FACE_SCAN_BYPASS_ALL=true
PRIVILEGED_FACE_VERIFICATION_ENABLED=false
EMAIL_TRANSPORT=disabled
```

The test suite seeds its own test data (school, users, roles) on startup and cleans it up after the session. Your existing data is not affected.

## What Is Tested

| File | Router | Tests |
|---|---|---|
| `test_health.py` | `/health` | 1 |
| `test_auth.py` | `/token`, `/login` | 5 |
| `test_users.py` | `/api/users` | 6 |
| `test_school.py` | `/api/school` | 4 |
| `test_school_settings.py` | `/api/school-settings` | 3 |
| `test_departments.py` | `/api/departments` | 4 |
| `test_programs.py` | `/api/programs` | 4 |
| `test_events.py` | `/api/events` | 6 |
| `test_attendance.py` | `/api/attendance` | 5 |
| `test_admin_import.py` | `/api/admin/import-students` | 4 |
| `test_governance.py` | `/api/governance` | 4 |
| `test_governance_hierarchy.py` | `/api/governance/units` | 4 |
| `test_sanctions.py` | `/api/sanctions` | 4 |
| `test_security_center.py` | `/api/auth/security` | 3 |
| `test_notifications.py` | `/api/notifications` | 3 |
| `test_audit_logs.py` | `/api/audit-logs` | 2 |
| `test_subscription.py` | `/api/subscription` | 2 |
| `test_reports.py` | `/api/attendance` (reports) | 4 |

**Total: 67 tests across 18 routers**

## What Is Skipped

Two routers are intentionally excluded from automated testing:

- **`face_recognition`** (`/api/face`) — requires InsightFace ONNX models (~500MB) and GPU/CPU inference. Not suitable for CI.
- **`public_attendance`** (`/public-attendance`) — depends on the face recognition runtime for the multi-face scan flow.

Both are covered by manual testing during deployment.

## How CI Works

GitHub Actions runs the suite on every push to `integrate/pilot-merge` using a `pgvector/pgvector:pg15` service container (matches production Docker image).

The CI job:
1. Spins up Postgres with `pgvector` extension
2. Creates `fastapi_db` and `ai_assistant` databases
3. Runs `alembic upgrade heads` to apply all migrations
4. Runs `pytest`

No real credentials are used — all env vars in CI are test-only values. The AI API key is never called during backend tests.

## Test Architecture

- **Seeded data** — `conftest.py` creates a test school, admin, campus_admin, and student user before tests run. Data is committed to the DB and cleaned up after the session.
- **No mocking** — tests hit the real FastAPI app with a real DB session. This catches schema mismatches, missing columns, and broken queries that unit tests would miss.
- **Auth** — tokens are obtained via the real `/login` endpoint using seeded credentials. No JWT is manually crafted.
- **Isolation** — each test file uses the shared session-scoped client and token fixtures. Tests that create data (departments, events, governance units) use unique identifiers to avoid conflicts across runs.

## Known Compatibility Fixes

The normalized schema (`aura_norm`) renamed several columns from the legacy schema. The following fixes were applied to make the backend work with the normalized schema:

- `Event.start_datetime` / `Event.end_datetime` → `Event.start_at` / `Event.end_at` in all query files (compatibility properties still exist on the model for non-query use)
- `Role.name` → `Role.code` in role lookup functions
- `user_face_profiles` table dropped — `has_face_reference_enrolled()` returns `False` gracefully; `security_center.py` wraps the query in try/except
- `School.logo_url`, `School.primary_color`, etc. — accessed via `getattr` with safe defaults in `school.py` and `school_settings.py`
- `StudentProfile.is_face_registered` / `registration_complete` — replaced with safe defaults (`False` / `True`) in user serialization

# Backend Testing Guide

<!--nav-->
[Previous](SECURITY_HARDENING.md) | [Next](../README.md) | [Home](/README.md)

---
<!--/nav-->


## Overview

The backend has a pytest suite of **195 tests** covering all router modules. Tests run against a real PostgreSQL database using the same schema as production. Celery tasks run synchronously in eager mode during tests â€” no Redis or worker process required.

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
pytest tests/test_import_lifecycle.py -v
```

### Prerequisites

- PostgreSQL running locally with `fastapi_db` database created
- All migrations applied: `alembic upgrade heads`
- Redis running locally (used by Celery in production; not required for tests since eager mode is enabled)
- `backend/.env` with at minimum:

```env
DATABASE_URL=postgresql://postgres:<password>@127.0.0.1:5432/fastapi_db
SECRET_KEY=any-string-for-local-testing
RATE_LIMIT_ENABLED=false
FACE_SCAN_BYPASS_ALL=true
PRIVILEGED_FACE_VERIFICATION_ENABLED=false
EMAIL_TRANSPORT=disabled
CELERY_TASK_ALWAYS_EAGER=true
```

The test suite seeds its own test data (school, users, roles) on startup and cleans it up after the session. Your existing data is not affected as long as you use a dedicated `fastapi_db` database for testing.

If tests fail due to leftover data from a previous run, reset the database:

```powershell
psql -U postgres -c "DROP DATABASE fastapi_db;"
psql -U postgres -c "CREATE DATABASE fastapi_db;"
alembic upgrade heads
```

## What Is Tested

| File | Coverage |
|---|---|
| `test_health.py` | Health and readiness endpoints |
| `test_auth.py` | Login, token, wrong password, unknown email |
| `test_auth_extended.py` | Password change, forgot password, reset requests, prompt dismiss |
| `test_users.py` | Get me, list users, create user, update profile |
| `test_users_extended.py` | Get by role, reset password, update roles, preferences, student account, delete profile |
| `test_users_accounts.py` | Get user by ID, delete user, get by role (all edge cases) |
| `test_school.py` | Get school, update branding, audit logs |
| `test_school_settings.py` | Get/update school settings |
| `test_school_admin.py` | Admin list schools, create school with IT account |
| `test_departments.py` | CRUD for departments |
| `test_programs.py` | CRUD for programs |
| `test_events.py` | CRUD for events |
| `test_events_extended.py` | Ongoing events, attendees, stats, time status, geolocation |
| `test_events_workflow.py` | Status patch, sign-out-early, attendees/stats edge cases |
| `test_attendance.py` | Manual check-in, duplicate, summary, records |
| `test_attendance_extended.py` | Bulk attendance, mark excused, face scan timeout, reports |
| `test_attendance_overrides.py` | Mark excused, mark absent no timeout (all edge cases) |
| `test_admin_import.py` | Preview valid/invalid, auth guards |
| `test_import_lifecycle.py` | Full import pipeline: preview â†’ commit â†’ job completes â†’ student created in DB |
| `test_face_recognition.py` | Auth guards and role checks (face bypass enabled) |
| `test_governance.py` | Governance access, settings |
| `test_governance_hierarchy.py` | Governance unit CRUD |
| `test_governance_data.py` | Data requests, retention, settings |
| `test_governance_members.py` | SSG setup, students, members, announcements |
| `test_sanctions.py` | List, view own, manage guards |
| `test_sanctions_extended.py` | Config, students, delegation, dashboard, export |
| `test_security_center.py` | Face status, sessions, auth guards |
| `test_security_extended.py` | Revoke session, revoke others, login history, face reference guards |
| `test_notifications.py` | List, mark read, auth guards |
| `test_notification_dispatch.py` | Missed events, low attendance, inbox, dispatch guards |
| `test_misc_extended.py` | Notification preferences, public attendance nearby events, health readiness |
| `test_public_attendance.py` | Nearby events, multi-face-scan (disabled/404/422 cases) |
| `test_audit_logs.py` | List audit logs, access control |
| `test_reports.py` | School attendance summary, student overview, stats |
| `test_subscription.py` | Get subscription, auth guard |
| `test_subscription_extended.py` | Update subscription, reminders |

**Total: 195 tests across all routers**

## What Is Not Fully Tested

- **Face recognition inference** â€” `FACE_SCAN_BYPASS_ALL=true` bypasses InsightFace model loading. The auth guards and role checks are tested, but actual embedding extraction and matching are not. These require real photos and a loaded ONNX model (~500MB).
- **Public attendance multi-face-scan happy path** â€” only error cases (disabled feature, missing body, invalid event) are tested. The full scan flow requires face embeddings.
- **WebSocket/SSE real-time delivery** â€” notification push over persistent connections is not testable with the synchronous `TestClient`.

## Celery Eager Mode

Celery tasks run synchronously during tests via `CELERY_TASK_ALWAYS_EAGER=true`. This means:

- `process_student_import_job.delay(job_id)` executes immediately in the same thread
- The import job completes before the test assertion runs
- No Redis broker or Celery worker process is needed

This is set automatically in `conftest.py` for local runs and in `ci.yml` for CI. Do not remove it â€” without it, import lifecycle tests will see jobs stuck in `pending` state.

## How CI Works

GitHub Actions runs the suite on every push and PR to `integrate/pilot-merge` using a `pgvector/pgvector:pg15` service container and a `redis:7-alpine` service container.

The CI job:
1. Spins up Postgres (`pgvector`) and Redis
2. Creates `fastapi_db` and `ai_assistant` databases
3. Runs `alembic upgrade heads`
4. Runs `pytest` with `CELERY_TASK_ALWAYS_EAGER=true`

No real credentials are used. The AI API key is never called during backend tests.

## Test Architecture

- **Seeded data** â€” `conftest.py` creates a test school, admin, campus_admin, and student user before tests run. Data is committed and cleaned up after the session.
- **No mocking** â€” tests hit the real FastAPI app through Starlette's `TestClient` (in-process ASGI, no network). This catches schema mismatches, missing columns, and broken queries that unit tests would miss.
- **Auth** â€” tokens are obtained via the real `/login` endpoint using seeded credentials. No JWT is manually crafted.
- **Shared session** â€” the `db_session` fixture is `scope="session"` and shared across all tests. Tests that need to see rows committed by internal service sessions (e.g. import) must use a fresh `SessionLocal()` context, not `db_session`.
- **Persistent local DB** â€” unlike CI (which starts fresh every run), your local `fastapi_db` persists between runs. Tests that insert rows with fixed identifiers (e.g. session JTIs) use `uuid4()` to avoid unique constraint violations on re-runs.


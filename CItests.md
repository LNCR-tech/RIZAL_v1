# CI Tests Documentation

Last updated: 2026-05-26

This document explains what the current GitHub Actions CI checks in the Aura
repository, how each job tests the system, and which major workflows are covered.

## Important Push Note

Pushing this file on `integrate/pilot-merge` will run `.github/workflows/ci.yml`
because that workflow runs on every push to `integrate/pilot-merge`.

The Flutter workflow `.github/workflows/aura-app-ci.yml` also runs on normal
pushes to `main`, `develop`, `feature/*`, and `integrate/pilot-merge`, so a
docs-only push can be used to exercise the main CI plus Flutter CI without
touching app code.

## Workflow Summary

### `.github/workflows/ci.yml` - Continuous Integration

Runs on:
- Pushes to `main`, `develop`, `feature/*`, and `integrate/pilot-merge`
- Pull requests into `main`, `develop`, and `integrate/pilot-merge`
- Manual `workflow_dispatch`

Main jobs:
- `security-audit`
- `backend-tests`
- `frontend-tests`
- `assistant-tests`
- `e2e-tests` (currently only runs on branch `pilot`)
- `docker-build-test`

### `.github/workflows/aura-app-ci.yml` - Aura App Flutter CI

Runs on:
- Pushes to `main`, `develop`, `feature/*`, and `integrate/pilot-merge`
- Pull requests that touch `frontend-app/**`
- Pull requests that touch `.github/workflows/aura-app-ci.yml`
- Manual `workflow_dispatch`

Main jobs:
- `analyze-test`
- `build-android`

### CD Workflows

`production-cd.yml` is active for pushes to `main` and manual dispatch.
It does not run when pushing to `integrate/pilot-merge`.

`staging-cd.yml` and `hotfix-cd.yml` are manual/disabled-style workflows.

## Continuous Integration Jobs

### Security & Dependency Audit

Workflow job: `security-audit`

What it installs:
- Node.js 20

What it runs:
```bash
cd frontend-web
npm audit --audit-level=high
```

What this catches:
- High-severity npm dependency vulnerabilities in `frontend-web`
- Dependency issues that would make the web frontend unsafe to ship

It also runs a simple hardcoded-secret scan:
```bash
grep -rE "(api_key|password|secret)\s*=\s*['\"][^'\"]+['\"]" backend/app/
```

What this catches:
- Obvious hardcoded `api_key`, `password`, or `secret` assignments in backend
  application code

What it does not replace:
- A full secret scanner
- Manual review of `.env` files
- GitGuardian or GitHub secret scanning

## Backend CI

Workflow job: `backend-tests`

Services started by GitHub Actions:
- PostgreSQL using `pgvector/pgvector:pg15`
- Redis using `redis:7-alpine`

Environment:
```text
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/fastapi_db
SECRET_KEY=test-secret-key
FACE_SCAN_BYPASS_ALL=true
```

What it installs:
```bash
cd backend
pip install -r requirements.txt
pip install flake8 pytest pytest-cov
```

What it runs:
```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
psql -h 127.0.0.1 -U postgres -c "CREATE DATABASE fastapi_db;"
alembic upgrade head
pytest tests/ --cov=app --cov-report=xml
```

What this catches:
- Syntax-level Python errors
- Undefined names and critical flake8 errors
- Broken Alembic migrations
- Multiple Alembic heads
- Schema/model mismatch against a fresh PostgreSQL database
- Backend API regressions
- Backend business-rule regressions
- Response validation failures from FastAPI/Pydantic
- Role and permission regressions
- Database constraint regressions

Coverage artifact:
- Uploads `backend/coverage.xml` as `backend-coverage`

### Backend Test Style

The backend tests are automated API tests, similar in purpose to Postman tests
but written as pytest code. They call FastAPI endpoints through `TestClient`,
using requests such as:

```python
client.get(...)
client.post(...)
client.patch(...)
client.delete(...)
```

CI has recently shown about 300 backend pytest cases. The exact number can
change because parametrized pytest cases expand into multiple test cases.

### Backend Test Fixtures

Backend tests use `backend/tests/conftest.py`.

It seeds:
- Test school
- Departments and programs
- Role records
- Admin user
- Campus admin user
- Student users for year-level cases
- Seed event and event target data
- Attendance status and method lookup rows

Common seeded users:
- `admin@test.com`
- `campus_admin@test.com`
- `student@test.com`
- `student_year2@test.com`
- `student_year5@test.com`

Testing behavior:
- Email delivery disabled
- Rate limiting disabled or fail-open
- Face scan bypass enabled
- Test auth tokens generated through real login endpoints

## Backend Coverage By Feature

### Authentication And Account Access

Files:
- `backend/tests/test_auth.py`
- `backend/tests/test_auth_extended.py`
- `backend/tests/test_google_auth.py`
- `backend/tests/test_google_auth_service.py`
- `backend/tests/test_security_negative.py`

What is tested:
- Valid login
- Wrong password rejection
- Unknown email rejection
- OAuth2 token endpoint
- Protected endpoint without token
- Change password
- Forgot-password request
- Password reset request listing
- Password change prompt dismissal
- Google login success
- Google login rejected for unregistered email
- Google login rejected for unverified email
- Google login disabled path
- Invalid Google token path
- Expired or tampered token rejection
- SQL injection style login payload rejection
- XSS-style event payload rejection

### RBAC And Authorization

Files:
- `backend/tests/test_rbac_matrix.py`
- `backend/tests/test_security_negative.py`
- `backend/tests/test_users.py`
- `backend/tests/test_users_extended.py`
- `backend/tests/test_users_accounts.py`

What is tested:
- Public route access
- Admin-only route access
- Campus admin route access
- Student route access
- Unauthenticated access failures
- Cross-user and cross-school data access blocking
- User listing permissions
- User detail permissions
- User role update permissions
- User deletion permissions
- Password reset permissions

### Events And Event Targets

Files:
- `backend/tests/test_events.py`
- `backend/tests/test_events_extended.py`
- `backend/tests/test_events_workflow.py`
- `backend/tests/test_event_target_permissions.py`
- `backend/tests/test_event_api_edge_cases.py`
- `backend/tests/test_year_level_filtering.py`
- `backend/tests/test_event_announcement_notifications.py`

What is tested:
- Event list
- Event detail
- Event create
- Event update
- Event delete
- Student cannot create events
- Unauthenticated user cannot create events
- Event status update
- Event attendees endpoint
- Event stats endpoint
- Event time-status endpoint
- Event location verification endpoint
- Sign-out open-early workflow
- Timezone normalization
- Audience scopes:
  - all
  - year level
  - department
  - course/program
  - department plus year
  - course/program plus year
- Governance target permission rules for SSG, SG, and ORG users
- Invalid year levels rejected
- Incomplete geofence fields rejected
- Overlong idempotency key rejected
- Year-level event filtering against student profiles
- Announcement notification recipients based on event target scope

### Attendance

Files:
- `backend/tests/test_attendance.py`
- `backend/tests/test_attendance_logic.py`
- `backend/tests/test_attendance_extended.py`
- `backend/tests/test_attendance_overrides.py`
- `backend/tests/test_scan_audit_log.py`
- `backend/tests/test_automation_backlog_core.py`

What is tested:
- Student own attendance records
- Event attendance report
- Manual check-in
- Duplicate check-in blocking
- Attendance summary
- Attendance before event open is blocked
- Bulk attendance
- Mark excused
- Mark absent without timeout
- Face-scan timeout auth checks
- Student attendance report and stats
- Geofence accepts inside-radius location
- Geofence rejects outside-radius location
- Rejected scan audit logging
- Rejected scan does not create attendance
- Rejected scan not appearing in attendance report
- Accepted scan behavior remains unchanged

### Face Recognition And Security Center

Files:
- `backend/tests/test_face_recognition.py`
- `backend/tests/test_security_center.py`
- `backend/tests/test_security_extended.py`
- `backend/tests/test_automation_backlog_core.py`

What is tested:
- Face registration requires auth
- Face registration is student-only
- Face scan with recognition requires student context
- Face scan with recognition requires auth
- Face verification status endpoint
- Active session listing
- Revoke other sessions
- Revoke specific session
- Login history
- Face reference auth checks
- Face verify auth checks
- Privileged login face requirement when MFA policy is enabled
- Privileged face bypass behavior in test mode

### Student, School, Department, Program, And Import Management

Files:
- `backend/tests/test_students_extended.py`
- `backend/tests/test_school.py`
- `backend/tests/test_school_admin.py`
- `backend/tests/test_school_settings.py`
- `backend/tests/test_departments.py`
- `backend/tests/test_programs.py`
- `backend/tests/test_admin_import.py`
- `backend/tests/test_bulk_import.py`
- `backend/tests/test_import_lifecycle.py`

What is tested:
- Student creation
- Student year-level validation
- Student status validation
- Default active student status
- School detail
- School branding update
- Student cannot update school settings
- School audit logs
- Admin school listing
- School IT account listing
- School IT creation
- School settings get/update
- Department CRUD
- Program CRUD
- Import preview
- Invalid import file handling
- Student cannot import
- Import template download
- Import job creation
- Import job status
- Imported student creation
- Import error download
- Retry failed import
- Preview error download
- Preview invalid-row removal

### Governance

Files:
- `backend/tests/test_governance.py`
- `backend/tests/test_governance_data.py`
- `backend/tests/test_governance_hierarchy.py`
- `backend/tests/test_governance_members.py`

What is tested:
- Governance access lookup
- Governance settings
- Student governance access behavior
- Governance auth requirements
- Data requests create/list/update
- Retention dry-run
- Governance unit list/detail/update
- Student cannot create governance unit
- SSG setup endpoint
- Governance student search
- Governance student listing
- Assign governance member
- Update governance member
- Delete governance member
- Create/list/update/delete announcements
- Announcements monitor
- Student blocked from announcement monitor

### Notifications

Files:
- `backend/tests/test_notifications.py`
- `backend/tests/test_notification_dispatch.py`
- `backend/tests/test_event_announcement_notifications.py`
- `backend/tests/test_misc_extended.py`

What is tested:
- Notification inbox
- Mark all read
- Notification auth requirement
- Dispatch missed events
- Dispatch low attendance
- Dispatch requires admin
- Dispatch requires auth
- Notification preferences get/update
- Test notification endpoint
- Event announcement dispatch summary
- Event announcement recipient filtering
- Event announcement school boundary enforcement
- Nonexistent event returns 404

### Sanctions, Reports, Subscription, Health, And Database Integrity

Files:
- `backend/tests/test_sanctions.py`
- `backend/tests/test_sanctions_extended.py`
- `backend/tests/test_reports.py`
- `backend/tests/test_subscription.py`
- `backend/tests/test_subscription_extended.py`
- `backend/tests/test_health.py`
- `backend/tests/test_misc_extended.py`
- `backend/tests/test_production.py`
- `backend/tests/test_database_integrity.py`
- `backend/tests/test_migrations.py`
- `backend/tests/test_performance_smoke.py`
- `backend/tests/test_api_contract.py`

What is tested:
- Sanctions dashboard
- Student own sanctions
- Student cannot manage sanctions
- Sanction config get/update
- Sanction student listing
- Sanction delegation
- Sanction export auth
- School attendance summary
- Student overview
- Student attendance stats
- Reports require auth
- Subscription get/update
- Subscription reminder runner
- Health and readiness endpoints
- Production-readiness smoke checks
- Unique constraints
- Foreign key constraints
- No duplicate migration heads
- Migrations apply cleanly
- Login, `me`, and event-list performance smoke checks
- API response shape for token, users/me, and events list

## Frontend Web CI

Workflow job: `frontend-tests`

What it installs:
```bash
cd frontend-web
npm ci
```

What it runs:
```bash
npm run lint
npm run typecheck
npm run test:unit
```

What this catches:
- ESLint errors
- Unused imports if configured through lint rules
- Vue/TypeScript type errors
- Unit test failures
- Broken helper functions and component contracts

### Frontend Web Unit Test Coverage

Files under `frontend-web/tests/unit/` cover:
- URL/base URL resolution
- Location display formatting
- Event editor target/audience logic
- Device permission helpers
- Navigation item definitions
- Attendance permission gate behavior
- Base button behavior
- Event location picker behavior
- Event editor sheet year-level/audience behavior

### Frontend Web Playwright E2E

Files exist under:
- `frontend-web/e2e/`
- `frontend-web/e2e/workflows/`

These include:
- Preview smoke tests
- Frontend-backend workflow tests
- RBAC tests
- Session tests
- Role route safety
- Expected UI action tests
- UI quality tests
- Pressable coverage tests

Current CI behavior:
- The `e2e-tests` job in `.github/workflows/ci.yml` only runs when
  `github.ref == 'refs/heads/pilot'`.
- This means Playwright E2E is skipped on `integrate/pilot-merge`.

When E2E runs on `pilot`, CI:
- Starts PostgreSQL and Redis
- Installs backend and assistant dependencies
- Installs frontend dependencies
- Installs Playwright Chromium
- Runs Alembic migrations
- Seeds the E2E database
- Starts backend on `127.0.0.1:8000`
- Starts assistant on `127.0.0.1:8500`
- Builds and previews frontend on `127.0.0.1:4173`
- Runs `npx playwright test`
- Uploads Playwright reports, test results, and service logs

## Flutter App CI

Workflow: `.github/workflows/aura-app-ci.yml`

### Analyze And Widget/Unit Tests

Workflow job: `analyze-test`

What it installs:
```bash
cd frontend-app
flutter pub get
```

What it runs:
```bash
flutter analyze
flutter test
```

What this catches:
- Dart analyzer errors
- Flutter analyzer errors
- Widget test failures
- Unit test failures
- Model/parser regressions
- Routing logic regressions
- UI semantics/layout test failures
- Shader compilation problems that appear during Flutter test loading

### Current Flutter Test Coverage

Files under `frontend-app/test/` cover:
- AuraButton widget behavior
- Login UI quality checks
- Mobile/tablet/desktop layout exception checks
- Accessibility semantics labels
- Bottom navigation tab behavior
- Event editor save flow
- Router redirect logic
- Auth metadata parsing
- Role normalization and priority
- Event editor draft logic
- Event editor payload creation and validation
- Attendance scan request building
- Geolocation permission behavior
- Repository API path and body construction
- App models and report parsing
- Governance model parsing
- Admin model parsing
- School/import model parsing
- Help Center catalogue/search/audience filtering
- Navigation item definitions
- Pagination helpers
- Location display helpers
- Color contrast helpers

### Flutter Integration Tests

File:
- `frontend-app/integration_test/app_e2e_test.dart`
- `frontend-app/integration_test/real_backend_e2e_test.dart`

What it contains:
- Signed-out app lands on login and exposes controls
- Student shell tab navigation
- Event editor edit flow saves through the event repository
- Real-backend mobile smoke path: student logs in through the Flutter UI,
  opens the Schedule tab, loads the seeded backend event, and opens event detail

Current CI behavior:
- `flutter test integration_test -d emulator-5554` runs inside the Android
  emulator job, because Flutter integration tests need a real connected device
  and cannot run against the Linux runner's web device.
- The mocked-provider integration tests still verify app-level user flows
  without depending on the backend.
- The real-backend E2E test is skipped by default unless
  `--dart-define=AURA_RUN_BACKEND_E2E=true` is supplied.
- In CI, `.github/workflows/aura-app-ci.yml` starts PostgreSQL, Redis, applies
  Alembic migrations, seeds the backend test data, starts FastAPI on port
  `8000`, then runs the Flutter app against `http://10.0.2.2:8000`.

### Android APK Build And Launch Smoke

Workflow job: `build-android`

What it installs:
- Python 3.12 and backend dependencies for the mobile E2E backend
- Java 17
- Flutter stable
- Flutter dependencies

What it runs:
```bash
cd backend
pip install -r requirements.txt
psql -h 127.0.0.1 -U postgres -c "CREATE DATABASE fastapi_db;"
alembic upgrade head
python - <<'PY'
from app.core.database import SessionLocal
from tests.conftest import _seed

db = SessionLocal()
try:
    _seed(db)
    db.commit()
finally:
    db.close()
PY
uvicorn app.main:app --host 0.0.0.0 --port 8000

cd frontend-app
flutter pub get
flutter build apk --debug \
  --dart-define=AURA_API_BASE_URL=http://10.0.2.2:8000 \
  --dart-define=AURA_API_TIMEOUT_MS=30000
```

Then it runs an Android emulator:
- API level 35
- x86_64
- Pixel 6 profile

Inside the emulator job, CI:
- Runs `flutter test integration_test -d emulator-5554` with
  `AURA_RUN_BACKEND_E2E=true`
- Installs `build/app/outputs/flutter-apk/app-debug.apk`
- Launches `com.aura.aura_app/.MainActivity`
- Waits 10 seconds
- Checks `adb shell pidof com.aura.aura_app`
- Dumps recent `logcat` output on failure
- Uploads `backend/backend.log` as a short-retention artifact

What this catches:
- Flutter integration test failures from `frontend-app/integration_test/`
- Student login regressions between the Flutter app and the real FastAPI backend
- Mobile API base URL wiring failures
- Backend seeded event visibility regressions in the Flutter schedule
- Event-detail navigation failures after loading backend data
- Android build failures
- Gradle/native build failures
- Flutter dependency/codegen issues
- APK install failures
- App launch crashes
- Immediate runtime crash after launch

What it does not prove:
- Every screen navigation path
- Every workflow inside the separately installed smoke-test APK
- Production deployed-server health

## Assistant CI

Workflow job: `assistant-tests`

What it installs:
```bash
cd assistant
pip install -r requirements.txt
```

Environment:
```text
SECRET_KEY=test-secret-key
ASSISTANT_DB_URL=sqlite:///./test_assistant_ci.db
AI_API_KEY=test-key
AI_API_BASE=https://test.example.com/v1
AI_MODEL=test-model
BACKEND_API_BASE_URL=http://localhost:8000
```

What it runs:
```bash
pytest tests/
```

What this catches:
- Assistant health endpoint regressions
- Conversation CRUD regressions
- Streaming/SSE response regressions
- Token/auth failures
- Invalid/missing auth handling
- Daily quota behavior
- Tool-call event behavior
- Deterministic data-answer behavior
- Chart/visual payload behavior
- MCP query safety behavior
- Backend JWT acceptance/rejection behavior in assistant integration tests

Assistant test files:
- `assistant/tests/test_health.py`
- `assistant/tests/test_conversations.py`
- `assistant/tests/test_stream.py`
- `assistant/tests/test_deterministic_ai_behaviour.py`
- `assistant/tests/test_integration.py`

## Auth Coverage Across The Whole System

Backend tests cover:
- Email/password login
- OAuth token endpoint
- Protected endpoints without token
- Wrong password
- Unknown email
- Tampered token
- Expired token
- Password change
- Forgot-password request
- Password reset request listing/approval paths
- Google login success/failure cases
- Privileged face verification policy behavior
- Role-based route access

Frontend app tests cover:
- Signed-out routing to login
- Password-change gate routing
- Privileged face-verification gate routing
- Role-based workspace redirect logic
- Login control semantics
- Password visibility interaction
- Empty login validation
- Google sign-in not-configured UI response

Frontend web tests cover:
- Unit-level session/url/navigation helpers
- Playwright session and route-safety tests exist but are skipped on
  `integrate/pilot-merge`

Assistant tests cover:
- Backend JWT acceptance
- Tampered JWT rejection
- Missing auth rejection
- Stream endpoint auth behavior
- Conversation isolation between users

## Docker Build Validation

Workflow job: `docker-build-test`

What it runs:
```bash
docker compose config --quiet
docker compose build
```

What this catches:
- Invalid `docker-compose.yml` syntax
- Missing build contexts
- Broken Dockerfiles
- Dependency install failures during image build
- Service build breakage before deployment

What it does not do:
- Start the full production stack
- Run migrations inside the built containers
- Run app health checks against built containers

## Production CD Quality Gates

Workflow: `.github/workflows/production-cd.yml`

Runs on:
- Pushes to `main`
- Manual `workflow_dispatch`

Does not run on:
- `integrate/pilot-merge`

Production CD has its own quality gates before deployment:
- Starts PostgreSQL and Redis
- Installs backend dependencies
- Runs flake8 syntax-critical checks
- Runs Alembic migrations
- Runs backend tests
- Validates `docker-compose.prod.yml`
- Builds production `migrate` and `assistant` images
- Deploys to VPS only after those gates pass
- Verifies backend and assistant health after deploy

## What CI Does Not Fully Guarantee Yet

CI is strong on backend API behavior, backend migrations, frontend web unit
tests, assistant behavior, Docker builds, Flutter analyzer/unit/widget tests,
and Flutter APK build/launch.

Current gaps:
- No strict endpoint-by-endpoint API coverage audit.
- Playwright E2E is skipped on `integrate/pilot-merge`.
- Flutter now has one real-backend mobile E2E smoke path, but it is not yet a
  complete mobile workflow suite for every role and feature.

## Practical Interpretation

The backend has the broadest automated coverage. It tests the real API through
FastAPI request calls and covers the core system behavior: auth, RBAC, events,
event targeting, attendance, imports, governance, notifications, sanctions,
reports, migrations, and database constraints.

The frontend web CI covers static quality, type safety, and unit-level behavior.
Full browser E2E exists but is not active on `integrate/pilot-merge`.

The Flutter app CI covers static analysis, widget/unit tests, Flutter
integration tests, and APK build/install/launch.

The assistant CI covers service health, auth, conversations, streaming, tool
events, deterministic data answers, chart payloads, and MCP safety.

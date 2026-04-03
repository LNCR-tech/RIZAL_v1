# Automated Tester Actions (API Runner)

This runner simulates user actions using HTTP calls (not UI clicks).

## Default Action Flow

1. Wait for `/health` to return `200`.
2. Admin login (`/token`).
3. Admin creates a school + campus admin account (`/api/school/admin/create-school-it`).
4. Admin resets the campus admin password (`/api/school/admin/school-it-accounts/{id}/reset-password`).
5. Campus admin login (`/token`) and change-password (`/auth/change-password`).
6. Campus admin creates:
   - department (`POST /api/departments/`)
   - program (`POST /api/programs/`)
   - event (`POST /api/events/`) (suite: `events`)
   - student user (`POST /api/users/`)
   - student profile (`POST /api/users/admin/students/`)
   - resets student password (`POST /api/users/{id}/reset-password`)
7. Governance checks (suite: `governance`):
   - `/api/governance/ssg/setup`
   - assign student member (`POST /api/governance/units/{id}/members`)
   - list units + event defaults + students
8. Student login (`/token`) and change-password (`/auth/change-password`).
9. Bulk import preview (suite: `bulk`): `POST /api/admin/import-students/preview`
10. Cross-tenant isolation (suite: `security`): a second campus admin attempts to read the first school's student.

## Logs Produced

Outputs PSV logs into `cmpj/` (by default):

- `logs_core_api.psv`
- `logs_security.psv`
- `logs_bulk_ops.psv`
- `logs_biometrics.psv`

## Running (Local Host)

```powershell
python cmpj/auto_tests/run_tests.py --base-url http://localhost:8000
```

## Running (Docker)

This repo includes a Docker Compose service `auto_tests` (profile `test`).

```powershell
docker compose --profile test run --rm auto_tests
```

Override suites:

```powershell
docker compose --profile test run --rm -e TEST_SUITES=health,core,governance auto_tests
```


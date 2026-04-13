# Backend Change Log

This file records backend behavior changes that should stay visible after code merges.

## Documentation Rule

For every backend code change in `Backend/`, update this file.

At minimum include:

- date
- purpose
- affected files
- route or schema changes
- migration or configuration impact

## 2026-04-13 - Add local Mailpit support via SMTP transport and Docker wiring

### Purpose

Enable local outbound email testing without real Gmail/OAuth credentials by adding SMTP transport support and a Mailpit service in local Docker Compose.

### Main files

- `Backend/app/core/config.py`
- `Backend/app/services/email_service/config.py`
- `Backend/app/services/email_service/transport.py`
- `Backend/scripts/send_test_email.py`
- `Backend/app/tests/test_email_service.py`
- `Backend/app/tests/test_config.py`
- `.env.example`
- `docker-compose.yml`
- `Backend/docs/EMAIL_FORMATS_EDITABLE.txt`
- `Backend/docs/BACKEND_EMAIL_LOCAL_TESTING_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added SMTP runtime settings to backend config:
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USERNAME`
  - `SMTP_PASSWORD`
  - `SMTP_USE_TLS`
  - `SMTP_USE_STARTTLS`
- extended email transport validation to support `EMAIL_TRANSPORT=smtp`
- added SMTP send and connection-check flow in email transport layer
- updated email summary/connectivity helpers to report host/port per active transport
- generalized test-email script messaging so it applies to both SMTP and Gmail API
- added tests for:
  - SMTP transport validation
  - SMTP send path
  - SMTP connectivity check path

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - backend can now send outbound email through SMTP in addition to Gmail API

### Migration impact

- no database migrations required
- local runtime configuration changed:
  - `docker-compose.yml` now includes `mailpit` service (`1025` SMTP, `8025` web UI)
  - local `backend`, `worker`, and `beat` services default to SMTP transport targeting `mailpit`

### How to test

1. Start local stack with mail services:
   - `docker compose up -d --build backend worker beat mailpit`
2. Run backend email tests:
   - `python -m pytest -q Backend/app/tests/test_email_service.py Backend/app/tests/test_config.py`
3. Send a test message:
   - `python Backend/scripts/send_test_email.py --recipient test@example.com`
4. Open Mailpit:
   - `http://localhost:8025`
   - verify email appears.

## 2026-04-13 - Generate unique temporary passwords per imported student account

### Purpose

Fix student bulk-import onboarding so each newly created student account receives its own unique temporary password in email, instead of one shared password for the entire import job.

### Main files

- `Backend/app/services/student_import_service.py`
- `Backend/app/repositories/import_repository.py`
- `Backend/app/tests/test_student_import_email_delivery.py`
- `Backend/app/tests/test_import_repository.py`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- removed shared import-job credential generation from `StudentImportService`
- now generates password credentials per row before batch insert:
  - `temporary_password` (email credential)
  - `password_hash` (stored user password)
- updated batch email queueing to use each inserted row's own `temporary_password`
- updated `ImportRepository.bulk_insert_students(...)` to use per-row `password_hash` values
- added a repository guard that raises a runtime error if a row reaches insertion without generated credentials
- added tests for:
  - per-row credential generation behavior
  - per-row password usage during onboarding email queueing
  - repository insertion validation with row-level password hashes

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - `POST /api/admin/import-students` now creates unique temporary passwords for each imported account email

### Migration impact

- no database migrations required
- no environment/configuration changes required

### How to test

1. Run import-related tests:
   - `python -m pytest -q Backend/app/tests/test_student_import_email_delivery.py Backend/app/tests/test_import_repository.py`
2. Perform a bulk student import with at least two new rows that have different email addresses.
3. Verify the onboarding emails show different temporary passwords per account.
4. Verify each imported user can log in only with the password sent to that specific email.

## 2026-04-12 - Stabilize first-login student face registration in Docker

### Purpose

Fix `POST /api/face/register` returning `503 Service Unavailable` during cold starts when InsightFace model files are still downloading or multiple workers initialize the runtime at the same time.

### Main files

- `Backend/app/services/face_engine/insightface_adapter.py`
- `Backend/app/main.py`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `Backend/docs/BACKEND_CHANGELOG.md`
- `Backend/docs/BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md`

### Backend changes

- added a cross-process model initialization lock around InsightFace startup so only one process performs first-time model initialization/download at a time
- added wait-and-retry behavior when another process is already warming the model bundle, instead of failing fast with generic initialization errors
- improved runtime reason handling with explicit warm-up state (`insightface_warming_up`) for pending model readiness
- triggered non-blocking face runtime warm-up during app startup via `FaceRecognitionService().face_recognition_status(mode="single")`
- face routes now return an explicit warm-up `503` quickly when the shared runtime warm-up thread is still running, instead of hanging until long model downloads finish
- added stale InsightFace init-lock recovery (PID-aware lock files plus age guard) so container restarts do not leave face warm-up permanently stuck behind orphaned lock files

### Runtime configuration changes

- local compose (`docker-compose.yml`):
  - backend now sets `UVICORN_WORKERS=1` to avoid multi-worker cold-start races in development
  - backend now mounts persistent InsightFace cache volume at `/root/.insightface`
- production compose (`docker-compose.prod.yml`):
  - backend now mounts persistent InsightFace cache volume at `/home/appuser/.insightface`

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - first-login face registration is less likely to fail with 503 during model warm-up in Docker deployments

### Migration impact

- no database migrations required
- Docker volume requirement added for InsightFace model cache persistence:
  - `insightface_models`

### How to test

1. Redeploy backend services:
   - `docker compose up -d --force-recreate backend`
2. Verify startup logs show face warm-up start/ready messages.
3. Login as a student and call `POST /api/face/register` with a valid face image:
   - expect success once model warm-up completes
   - repeated container restarts should no longer re-download the model every time when using the new cache volume.

## 2026-04-12 - Allow Excel import headers with trailing blank columns

### Purpose

Fix bulk import preview failures for valid Excel templates where spreadsheet formatting leaves extra empty header cells after the expected columns.

### Main files

- `Backend/app/services/import_validation_service.py`
- `Backend/app/tests/test_admin_import_preview_flow.py`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- updated `validate_headers(...)` to trim trailing empty normalized header cells before strict header comparison
- preserved strict validation for column names and order in the expected import template
- added an API-level test that uploads `.xlsx` with the expected headers plus trailing blank header columns

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - `POST /api/admin/import-students/preview` now accepts template headers with trailing blank columns

### Migration impact

- no database migrations required
- no configuration changes required

### How to test

1. Run import preview tests:
   - `python -m pytest -q Backend/app/tests/test_admin_import_preview_flow.py`
2. Upload an Excel file with template headers plus trailing blank columns and verify preview succeeds when row values are valid.

## 2026-04-12 - Fix Docker bulk-import worker file sharing in local compose

### Purpose

Fix import jobs failing in Docker because backend and worker containers were not guaranteed to use the same import storage path.

### Main files

- `docker-compose.yml`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- set `IMPORT_STORAGE_DIR=/tmp/valid8_imports` for local `backend`, `worker`, and `beat` services in `docker-compose.yml`
- aligned runtime import storage path with the shared `import_storage` Docker volume mount already configured at `/tmp/valid8_imports`
- prevents preview manifests/import payloads from being written to non-shared container-local paths (for example `/storage/imports`)

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior fix:
  - `POST /api/admin/import-students` jobs can now read preview/import files from the worker in local Docker deployments

### Migration impact

- no database migrations required
- local Docker environment behavior changed:
  - import artifacts are now consistently stored in the shared import volume path

### How to test

1. Redeploy local stack:
   - `docker compose up -d --force-recreate backend worker beat`
2. Upload a valid student import file, preview it, and start import.
3. Verify `/api/admin/import-status/{job_id}` advances beyond `pending/queued` and no `Uploaded file was not found on server` appears in worker logs.

## 2026-04-12 - Remove MFA login flow and MFA management endpoints

### Purpose

Remove MFA challenge-based authentication so login always returns a direct bearer session, and remove backend MFA management routes and email/task wiring tied to that flow.

### Main files

- `Backend/app/routers/auth.py`
- `Backend/app/services/auth_session.py`
- `Backend/app/services/security_service.py`
- `Backend/app/routers/security_center.py`
- `Backend/app/schemas/security.py`
- `Backend/app/services/auth_task_dispatcher.py`
- `Backend/app/workers/tasks.py`
- `Backend/app/services/email_service/__init__.py`
- `Backend/app/services/email_service/use_cases.py`
- `Backend/app/services/email_service/rendering.py`
- `Backend/app/services/email_service/config.py`
- `Backend/app/core/config.py`
- `Backend/app/schemas/auth.py`
- `Backend/app/tests/test_api.py`
- `Backend/app/tests/test_auth_task_dispatcher.py`
- `.env.example`
- `Backend/docs/BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md`
- `Backend/docs/EMAIL_FORMATS_EDITABLE.txt`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- removed email-code MFA login flow from `POST /login`
- removed `POST /auth/mfa/verify`
- removed MFA status management routes from security center
- removed MFA challenge generation/verification helpers from security service
- removed MFA task dispatch and worker task registrations
- removed MFA email template/use-case exports from the email service package
- login token issuance no longer returns face-pending sessions as an auth gate
- login history now records successful login auth method as `password` for login routes

### Route or schema impact

- removed route: `POST /auth/mfa/verify`
- removed routes: `GET /api/auth/security/mfa-status`, `PUT /api/auth/security/mfa-status`
- `POST /login` and `POST /token` now return direct bearer token payloads without MFA challenge fields
- token schema no longer includes:
  - `mfa_required`
  - `mfa_challenge_id`
  - `mfa_expires_at`

### Migration impact

- no database migration required
- existing `mfa_challenges`/`user_security_settings.mfa_enabled` data remains unused by auth flow

### Configuration impact

- removed `AUTH_ENABLE_MFA` from `.env.example` and backend runtime config parsing
- if `AUTH_ENABLE_MFA` is still present in existing deployments, it is ignored by current code

### How to test

1. Run auth regression tests:
   - `python -m pytest -q Backend/app/tests/test_api.py Backend/app/tests/test_auth_task_dispatcher.py`
2. Call `POST /token` and `POST /login` with valid credentials and verify:
   - `200 OK`
   - `access_token` is present
   - no MFA challenge response fields are returned
3. Verify removed endpoints now return `404`:
   - `POST /auth/mfa/verify`
   - `GET /api/auth/security/mfa-status`
   - `PUT /api/auth/security/mfa-status`

## 2026-04-12 - Align backend container Python runtime with pinned dependency constraints

### Purpose

Fix backend Docker build failures caused by a Python version mismatch between the container base image and pinned dependencies.

### Main files

- `Backend/Dockerfile`
- `Backend/Dockerfile.prod`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- changed backend base images from `python:3.10-slim` to `python:3.11-slim` for both development and production Dockerfiles
- no application logic changes; runtime image now matches requirements that need Python 3.11+ (for example `numpy==2.4.4`)

### Route or schema impact

- no route path changes
- no request/response schema changes

### Migration impact

- no migration changes
- container runtime requirement changed:
  - backend Docker images now require Python 3.11-compatible base image layers

### How to test

1. Build backend images:
   - `docker build -t rizal-backend:local -f Backend/Dockerfile Backend`
   - `docker compose -f docker-compose.prod.yml build backend worker beat`
2. Confirm dependency installation completes without `No matching distribution found for numpy==2.4.4`.
3. Start backend services and verify health/login endpoints respond normally.

## 2026-04-12 - Seed admin user into default school scope for onboarding endpoints

### Purpose

Prevent `403 Forbidden` responses on school-scoped setup endpoints (for example `GET /school-settings/me`) by ensuring the seeded platform admin is associated with the default school.

### Main files

- `Backend/app/seeder.py`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- changed `_apply_admin_defaults(...)` signature to accept `default_school_id`
- updated admin defaults logic to set `user.school_id` to the provided default school id
- updated `seed_admin_user(...)` to:
  - create new admin users with `school_id=school.id`
  - pass `school.id` when applying admin defaults
- removed the stale `del school` line in `seed_admin_user(...)` so the seeded school id is used

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime authorization behavior changes for school-scoped endpoints because seeded admin users are now school-associated

### Migration impact

- no migration changes
- existing databases may require one-time admin backfill if the admin record already has `school_id` as `NULL`

### How to test

1. Run seeding (`python seed.py`) on a clean database and confirm `admin@university.edu` is created with a non-null `school_id`.
2. Login as the seeded admin and call `GET /school-settings/me`; verify it returns `200` instead of `403`.
3. For existing DBs, update the admin row (example):
   `UPDATE users SET school_id = 1 WHERE email = 'admin@university.edu';`
   then retry `GET /school-settings/me`.

## 2026-04-11 - Canonicalize backend storage paths to repo-root for stable runtime behavior

### Purpose

Prevent duplicate storage roots (`storage/` vs `Backend/storage/`) by resolving relative storage config paths from the repository root instead of process working directory.

### Main files

- `Backend/app/core/config.py`
- `Backend/app/tests/test_config.py`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added storage path normalization in config:
  - relative `IMPORT_STORAGE_DIR` values now resolve from repo root
  - relative `SCHOOL_LOGO_STORAGE_DIR` values now resolve from repo root
- kept absolute storage paths supported unchanged
- added config tests covering:
  - env candidate path order
  - relative storage resolution behavior
  - absolute storage pass-through behavior
  - `get_settings()` normalized storage outputs

### Route or schema impact

- no route path changes
- no request/response schema changes

### Migration impact

- no migration changes
- runtime configuration behavior changed for relative storage paths:
  - set absolute paths explicitly if you need non-repo-root storage

### How to test

1. `python -m pytest -q Backend/app/tests/test_config.py`
2. `python -m pytest -q Backend/app/tests/test_admin_import_preview_flow.py`
3. Verify import previews/reports and school logo files are written under the single repo-root `storage/` tree when using relative env values.

## 2026-04-11 - Storage hygiene cleanup for import preview artifacts

### Purpose

Removed committed runtime preview artifacts from backend storage and documented the cleanup to keep repository state production-safe.

### Main files

- `Backend/storage/imports/previews/46defea3-52fe-4bdf-9542-5801f2643f8d.json` (deleted)
- `Backend/storage/imports/previews/8f269cd7-c431-4519-a923-0df524d2eb72.json` (deleted)
- `Backend/storage/imports/previews/c3a61c73-e7a6-413b-90d8-486c62133c31.json` (deleted)
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- removed generated import-preview manifest files from version control
- no API code path or behavior changed

### Route or schema impact

- no route path changes
- no request/response schema changes

### Migration impact

- no migration changes
- no runtime configuration changes

### How to test

1. `python -m pytest -q Backend/app/tests/test_admin_import_preview_flow.py`
2. Verify preview/import endpoints still create and consume manifests under configured `IMPORT_STORAGE_DIR`.

## 2026-04-11 - Reports validation cleanup: remove duplicate unused import-report helpers

### Purpose

Completed final reports validation cleanup by removing dead duplicate helper functions from `admin_import.py` that were already centralized under `app.reports.system.queries`.

### Main files

- `Backend/app/routers/admin_import.py`
- `Backend/docs/BACKEND_REPORTS_MODULE_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- removed unused duplicate functions:
  - `_build_retry_workbook_bytes`
  - `_build_preview_error_report_bytes`
- removed duplicate preview-manifest read/path logic from `admin_import.py` by reusing:
  - `app.reports.system.queries.preview_manifest_path`
  - `app.reports.system.queries.load_preview_manifest`
- kept all import/report endpoint behavior unchanged (route handlers already delegate report downloads/status to `app.reports.system.router`)

### Route or schema impact

- no route path changes
- no request/response schema changes

### Migration impact

- no migration changes
- no `.env` or runtime configuration changes

### How to test

1. `python -m pytest -q Backend/app/tests/test_admin_import_preview_flow.py`
2. `python -m pytest -q Backend/app/tests`
3. Verify import preview, import status, and failed-row download endpoints still return expected responses.

## 2026-04-11 - Refactor report APIs into modular `app/reports` architecture

### Purpose

Consolidated report-related backend behavior into a dedicated reports module with explicit router/service/query layers, while preserving existing report endpoint contracts.

### Main files

- `Backend/app/reports/attendance/router.py`
- `Backend/app/reports/attendance/service.py`
- `Backend/app/reports/attendance/queries.py`
- `Backend/app/reports/student/router.py`
- `Backend/app/reports/student/service.py`
- `Backend/app/reports/student/queries.py`
- `Backend/app/reports/school/router.py`
- `Backend/app/reports/school/service.py`
- `Backend/app/reports/school/queries.py`
- `Backend/app/reports/system/router.py`
- `Backend/app/reports/system/service.py`
- `Backend/app/reports/system/queries.py`
- `Backend/app/routers/attendance/reports.py`
- `Backend/app/routers/attendance/records.py`
- `Backend/app/routers/admin_import.py`
- `Backend/app/routers/audit_logs.py`
- `Backend/app/routers/notifications.py`
- `Backend/app/routers/governance_hierarchy.py`
- `Backend/docs/BACKEND_REPORTS_MODULE_GUIDE.md`

### Backend changes

- introduced dedicated `app/reports` package split by domain:
  - `attendance` for event-level attendance reporting and event attendance listings
  - `student` for student overview/report/stats/records flows
  - `school` for aggregate attendance summary
  - `system` for import report downloads/status, audit logs search, notification logs, and governance dashboard overview delegation
- moved report business logic from legacy router files into service/query layers
- reduced legacy report endpoints to thin wrappers/composition logic
- retained legacy router entry points in main app wiring
- added explicit reports registration in `Backend/app/main.py` via `include_api_router(reports_router)`
- removed report endpoint includes from `Backend/app/routers/attendance/__init__.py` to avoid duplicate route registration

### Route or schema impact

- no route path changes
- no response model contract changes
- no request payload contract changes

### Migration impact

- no migration changes
- no `.env` or runtime configuration changes

### How to test

1. `python -m compileall Backend/app/reports Backend/app/routers/attendance/reports.py Backend/app/routers/attendance/records.py Backend/app/routers/admin_import.py Backend/app/routers/audit_logs.py Backend/app/routers/notifications.py Backend/app/routers/governance_hierarchy.py`
2. `python -m pytest -q Backend/app/tests/test_admin_import_preview_flow.py Backend/app/tests/test_governance_hierarchy_api.py`
3. `python -m pytest -q Backend/app/tests/test_public_attendance.py`

## 2026-04-11 - Add sanctions Step 8 behavior tests under Backend/tests

### Purpose

Added explicit Step 8 sanctions behavior coverage in a dedicated backend test module to validate event-completion generation, scope enforcement, delegation impact, approval history logging, and student isolation.

### Main files

- `Backend/tests/test_sanctions.py`
- `Backend/docs/BACKEND_SANCTIONS_MANAGEMENT_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added `Backend/tests/test_sanctions.py` with scenarios for:
  - sanction record auto-generation after event completion workflow transition
  - scope enforcement (`SSG` sees all, `SG` sees scoped records, `ORG` sees scoped records)
  - delegation grant changing access results for event sanctions list
  - approve action creating compliance history records without duplicate history on re-approve
  - student `/api/sanctions/students/me` personal-view isolation
- made the new test module self-contained with local DB/client fixtures so it runs independently and alongside `Backend/app/tests/*` without pytest plugin collisions

### Route or schema impact

- no route path changes
- no request/response schema changes
- no database schema changes

### Migration impact

- no migration changes
- no `.env` changes required

### How to test

1. Run `python -m pytest -q Backend/tests/test_sanctions.py`.
2. Run `python -m pytest -q Backend/app/tests/test_sanctions_api.py Backend/app/tests/test_event_workflow_status.py Backend/tests/test_sanctions.py`.
3. Confirm all Step 8 sanctions scenarios pass.

## 2026-04-11 - Add sanctions management data model foundation

### Purpose

Added the initial sanctions management schema and model layer so sanctions configuration, sanction records, sanction items, delegation, compliance history, and clearance deadlines can be persisted.

### Main files

- `Backend/app/models/sanctions.py`
- `Backend/app/models/__init__.py`
- `Backend/alembic/versions/d1a2b3c4d5e6_add_sanctions_management_tables.py`
- `Backend/alembic/env.py`
- `Backend/app/tests/test_sanctions_models.py`
- `Backend/docs/BACKEND_SANCTIONS_MANAGEMENT_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added sanctions ORM models and status/scope enums:
  - `EventSanctionConfig`
  - `SanctionRecord`
  - `SanctionItem`
  - `SanctionDelegation`
  - `SanctionComplianceHistory`
  - `ClearanceDeadline`
- registered sanctions models in `app.models` package exports
- included sanctions model import in Alembic env so metadata-aware workflows include the new tables
- added schema-level tests for sanctions uniqueness constraints, enum defaults, and metadata registration

### Route or schema impact

- no HTTP route paths changed in this step
- database schema changed with six new sanctions tables and related enum types

### Migration impact

- requires `Backend/alembic/versions/d1a2b3c4d5e6_add_sanctions_management_tables.py`
- adds these tables:
  - `event_sanction_configs`
  - `sanction_records`
  - `sanction_items`
  - `sanction_delegations`
  - `sanction_compliance_history`
  - `clearance_deadlines`

### How to test

1. Run `alembic upgrade head` in `Backend/`.
2. Run `python -m pytest -q Backend/app/tests/test_sanctions_models.py`.
3. Confirm all sanctions model tests pass and the migration applies without schema errors.

## 2026-04-11 - Implement sanctions management routes, service rules, async emails, and event-completion generation

### Purpose

Implemented sanctions management backend behavior across routes, service logic, and worker dispatch, including delegation-aware access control and automatic sanctions generation after event completion.

### Main files

- `Backend/app/routers/sanctions.py`
- `Backend/app/schemas/sanctions.py`
- `Backend/app/services/sanctions_service.py`
- `Backend/app/main.py`
- `Backend/app/services/event_workflow_status.py`
- `Backend/app/routers/events/shared.py`
- `Backend/app/routers/events/crud.py`
- `Backend/app/routers/events/workflow.py`
- `Backend/app/workers/tasks.py`
- `Backend/app/tests/test_sanctions_api.py`
- `Backend/app/tests/test_event_workflow_status.py`
- `Backend/app/tests/test_auth_task_dispatcher.py`
- `Backend/docs/BACKEND_SANCTIONS_MANAGEMENT_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added sanctions router and mounted it under `/api/sanctions`
- added sanctions request/response schemas for config, delegation, student lists, dashboard, and clearance deadlines
- implemented sanctions service layer logic for all new sanctions endpoints (router stays thin)
- enforced governance scope and delegation checks per event with role-level rules:
  - SSG full sanctions read across governance levels
  - SSG sanctions write limited to SSG-owned events
  - SG sanctions access for SG-owned events plus per-event SSG delegation
  - ORG sanctions access for ORG-owned events plus per-event SG delegation
  - students only access their own sanctions through `/students/me`
- added delegation management behavior with creator-level checks and owner-level delegation constraints
- added Excel export behavior for event sanctions with department sheets, course grouping, and year sorting
- added Celery tasks for sanctions notification, clearance deadline warnings, and compliance confirmation email dispatch
- hooked sanctions auto-generation into event completion flow:
  - when attendance finalization runs for completed events and sanctions are enabled, absent students receive sanction records and async notification dispatch
  - sync summaries now include sanctions generation counters
- extended manual event-completion write paths to run sanctions generation after attendance finalization

### Route or schema impact

- new routes:
  - `GET /api/sanctions/events/{event_id}/config`
  - `PUT /api/sanctions/events/{event_id}/config`
  - `GET /api/sanctions/events/{event_id}/students`
  - `POST /api/sanctions/events/{event_id}/students/{user_id}/approve`
  - `GET /api/sanctions/events/{event_id}/delegation`
  - `PUT /api/sanctions/events/{event_id}/delegation`
  - `GET /api/sanctions/dashboard`
  - `GET /api/sanctions/students/me`
  - `GET /api/sanctions/students/{user_id}`
  - `POST /api/sanctions/clearance-deadline`
  - `GET /api/sanctions/clearance-deadline`
  - `GET /api/sanctions/events/{event_id}/export`
- event workflow sync summary payload now includes:
  - `sanction_records_created`
  - `sanction_notification_emails_queued`

### Migration impact

- no new migration in this step (uses tables from `d1a2b3c4d5e6_add_sanctions_management_tables.py`)
- no `.env` changes required

### How to test

1. Run `python -m pytest -q Backend/app/tests/test_sanctions_models.py Backend/app/tests/test_sanctions_api.py Backend/app/tests/test_auth_task_dispatcher.py Backend/app/tests/test_event_workflow_status.py`.
2. Verify sanctions config/delegation endpoints for SSG and SG roles.
3. Verify SG delegated event access and approve flow.
4. Verify `/api/sanctions/students/me` returns only current student sanctions.
5. Verify event completion flow creates sanctions for absent students when sanctions are enabled.

## 2026-04-11 - Add sanctions governance permissions and route-level sanctions permission guards

### Purpose

Added governance permission codes for sanctions management and enforced them at sanctions router level following existing governance route guard patterns.

### Main files

- `Backend/app/models/governance_hierarchy.py`
- `Backend/app/services/governance_hierarchy_service/shared.py`
- `Backend/app/services/governance_hierarchy_service/permissions.py`
- `Backend/app/services/governance_hierarchy_service/__init__.py`
- `Backend/app/routers/sanctions.py`
- `Backend/alembic/versions/e2f7a1c9d4b6_add_sanctions_governance_permissions.py`
- `Backend/app/tests/test_sanctions_api.py`
- `Backend/docs/BACKEND_SANCTIONS_MANAGEMENT_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added six sanctions-specific governance permission codes:
  - `view_sanctioned_students_list`
  - `view_student_sanction_detail`
  - `approve_sanction_compliance`
  - `configure_event_sanctions`
  - `export_sanctioned_students`
  - `view_sanctions_dashboard`
- added permission metadata entries in `PERMISSION_DEFINITIONS`
- added sanctions permission group constants in governance service shared module:
  - `SANCTIONS_MANAGEMENT_PERMISSION_GROUP`
  - `SANCTIONS_MANAGEMENT_PERMISSION_CODES`
- expanded unit permission whitelist for `SSG`, `SG`, and `ORG` to include sanctions permissions
- added route-level permission guards in sanctions router using governance patterns:
  - admin/campus_admin bypass
  - governance membership required for governance users
  - `ensure_governance_permission(...)` checks per action

### Route or schema impact

- route-level permission requirements were added to sanctions routes:
  - config and delegation routes require `configure_event_sanctions`
  - sanctioned students listing requires `view_sanctioned_students_list`
  - student sanctions detail requires `view_student_sanction_detail`
  - approve route requires `approve_sanction_compliance`
  - dashboard route requires `view_sanctions_dashboard`
  - export route requires `export_sanctioned_students`
- `GET /api/sanctions/students/me` remains student-only
- `GET /api/sanctions/clearance-deadline` remains available for student warning/popup flow

### Migration impact

- added migration `Backend/alembic/versions/e2f7a1c9d4b6_add_sanctions_governance_permissions.py`
- migration seeds six new rows into `governance_permissions`
- migration widens the `governance_permission_code` enum/check shape and narrows it on downgrade

### How to test

1. Run `alembic upgrade head` in `Backend/`.
2. Run `python -m pytest -q Backend/app/tests/test_sanctions_api.py`.
3. Verify sanctions endpoints return `403` for governance members lacking new sanctions permissions.
4. Verify sanctions endpoints succeed after granting the required permission codes.

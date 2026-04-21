[← Back to Main README](../../README.md)

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

## 2026-04-20 - Dev-safe default: disable outbound email in Docker Compose unless configured

### Purpose

Avoid forcing Gmail API configuration in local Docker runs. Outbound email is now disabled by default unless `EMAIL_TRANSPORT` is explicitly set.

### Main files

- `docker-compose.yml`
- `README.md`
- `Backend/docs/BACKEND_EMAIL_LOCAL_TESTING_GUIDE.md`

### Backend changes

- configuration-only change:
  - `docker-compose.yml` now defaults `EMAIL_TRANSPORT` to `disabled` for `backend`, `worker`, and `beat`
  - to enable outbound email locally, set `EMAIL_TRANSPORT=smtp` (Mailpit) or `EMAIL_TRANSPORT=gmail_api` (Gmail API) in the root `.env`

### Route or schema impact

- no route path changes
- no request/response schema changes

### Migration impact

- no database migrations required
- runtime configuration impact:
  - local Docker default no longer attempts to use Gmail API unless configured

### How to test

1. Run `docker compose config` and confirm `backend`, `worker`, and `beat` default `EMAIL_TRANSPORT` to `disabled`.
2. Enable Mailpit:
   - set `EMAIL_TRANSPORT=smtp`, `SMTP_HOST=mailpit`, `SMTP_PORT=1025`
   - run `docker compose up -d --build mailpit backend worker beat`
   - run `python Backend/scripts/send_test_email.py --recipient test@example.com` and verify message in `http://localhost:8025`

## 2026-04-18 - Prevent student stats/report 500s when `events.event_type` is absent

### Purpose

Fix `500` errors on student attendance stats/report queries in databases where the `events` table does not include an `event_type` column.

### Main files

- `Backend/app/reports/student/queries.py`
- `Backend/app/tests/test_api.py`
- `Backend/docs/BACKEND_REPORTS_MODULE_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added a schema-compatibility helper in student report queries to detect whether `Event.event_type` exists
- updated student report event-type filter behavior:
  - if `event_type` column exists, filtering/grouping uses that column
  - if `event_type` column is absent, queries no longer reference it
- updated student stats event-type breakdown behavior:
  - when `event_type` is absent, stats return a single bucket label `Regular Events` grouped by attendance status
- added regression test coverage for:
  - `GET /api/attendance/students/{student_id}/stats?group_by=month`
  - verifies route returns `200` and includes `Regular Events` breakdown without requiring schema changes

### Route or schema impact

- no route path changes
- no request schema changes
- runtime behavior change:
  - `GET /api/attendance/students/{student_id}/stats` no longer crashes on missing `event_type` column
  - `GET /api/attendance/students/{student_id}/report` ignores `event_type` filtering when the column is unavailable

### Migration impact

- no database migration required for this fix
- optional future schema enhancement remains possible (adding `events.event_type`) but is not required for report endpoints to function

### How to test

1. Run focused test:
   - `python -m pytest -q Backend/app/tests/test_api.py -k "student_attendance_stats_returns_200_without_event_type_column"`
2. Manual API check:
   - `GET /api/attendance/students/{student_profile_id}/stats?group_by=month`
   - confirm `200` and `event_type_breakdown` entries are returned.

## 2026-04-18 - Normalize legacy attendance method markers in report responses

### Purpose

Fix `500` errors on attendance report endpoints when historical seed rows contain non-enum method markers such as `seed_core` and `seed_duplicate_*`.

### Main files

- `Backend/app/routers/attendance/shared.py`
- `Backend/app/reports/attendance/service.py`
- `Backend/app/misamis_university_seeder.py`
- `Backend/app/tests/test_api.py`
- `Backend/docs/BACKEND_REPORTS_MODULE_GUIDE.md`
- `Backend/docs/BACKEND_LARGE_DATA_SEED_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added response-side normalization for attendance method values in shared attendance serializers:
  - valid values remain `face_scan` and `manual`
  - unsupported/legacy stored values now normalize to `manual` instead of raising a schema validation error
- added defensive status normalization in the same serializer path to keep report payloads schema-safe
- updated Misamis large seed generation so future attendance rows are created with `method='manual'`
- added API regression coverage for:
  - `GET /api/attendance/events/{event_id}/attendances-with-students`
  - verifies legacy `seed_duplicate_2` stored method serializes as `manual` and endpoint returns `200`

### Route or schema impact

- no route path changes
- no request schema changes
- runtime behavior change for attendance responses using shared attendance serialization:
  - legacy invalid stored method markers no longer cause `500`
  - responses now emit schema-valid method values

### Migration impact

- no database migration required
- no environment/configuration changes required
- optional operational cleanup for existing data:
  - `UPDATE attendances SET method = 'manual' WHERE method LIKE 'seed_%';`

### How to test

1. Run focused backend tests:
   - `python -m pytest -q Backend/app/tests/test_api.py -k "attendance_with_students_normalizes_legacy_seed_method_values"`
2. Call:
   - `GET /api/attendance/events/{event_id}/attendances-with-students`
   with an event that includes historical `seed_*` attendance methods and confirm `200`.
3. Optional DB cleanup:
   - run `UPDATE attendances SET method = 'manual' WHERE method LIKE 'seed_%';`
   - restart backend and verify attendance report endpoints still return `200`.

## 2026-04-18 - Prevent users endpoint 500s from reserved-domain seed emails

### Purpose

Fix runtime `500` errors on user profile/list routes when seeded accounts contain reserved-domain emails (for example `*.seed.local`) that fail strict response `EmailStr` validation.

### Main files

- `Backend/app/schemas/user.py`
- `Backend/app/routers/users/shared.py`
- `Backend/app/tests/test_api.py`
- `Backend/app/misamis_university_seeder.py`
- `Backend/docs/BACKEND_LARGE_DATA_SEED_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- changed output user schema typing so response payloads treat `email` as a string instead of re-validating with `EmailStr`
- kept input validation strict for account-creation flows:
  - `UserCreate.email` remains `EmailStr`
  - `StudentAccountCreate.email` remains `EmailStr`
- retained users payload slimming behavior (`student_profile.attendances` remains `[]` on users endpoints)
- updated Misamis large-seed generated email domain from `misamisu.seed.local` to `misamisu.seed.edu.ph` for future seed compatibility with strict validators
- extended regression coverage to ensure `/api/users/` and `/api/users/me/` succeed with seeded-style `.local` addresses already present in the database

### Route or schema impact

- no route path changes
- response schema behavior update on users endpoints:
  - `User*` response payloads now expose `email` as a plain string field
- request validation remains unchanged for create/update routes that already enforce email format

### Migration impact

- no database migration required
- no environment/configuration changes required
- existing databases with previously seeded `.local` emails now work on users endpoints without data cleanup

### How to test

1. Run focused tests:
   - `python -m pytest -q Backend/app/tests/test_api.py -k "users_endpoints_do_not_expand_student_attendance_history or get_all_users_returns_paged_student_profiles"`
2. Login as a user seeded with a `.local` email and call:
   - `GET /api/users/me/`
   - `GET /api/users/` (admin/campus_admin)
   confirm both return `200`.

## 2026-04-18 - Keep users API payloads summary-only for student profiles

### Purpose

Prevent `/api/users/` and `/api/users/me/` from failing on large seeded datasets and reduce response size by avoiding full attendance-history expansion inside user profile payloads.

### Main files

- `Backend/app/routers/users/shared.py`
- `Backend/app/tests/test_api.py`
- `Backend/docs/BACKEND_USER_PREFERENCES_AND_AUTH_SESSION_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- changed user serialization so `student_profile` is built from explicit profile fields only
- stopped loading/serializing `student_profile.attendances` in users endpoints
- kept response compatibility by returning `student_profile.attendances` as an empty list in users payloads
- added regression coverage that inserts attendance rows with non-API method markers (for example `seed_core`) and verifies users endpoints still return `200`

### Route or schema impact

- no route path changes
- no request schema changes
- runtime response behavior update for:
  - `GET /api/users/`
  - `GET /api/users/me/`
  - `GET /api/users/{user_id}`
  - `PATCH /api/users/{user_id}`
  - `PUT /api/users/{user_id}/roles`
  these routes now return student profile summary fields only and do not embed historical attendance rows

### Migration impact

- no database migration required
- no environment/configuration changes required

### How to test

1. Run focused regression tests:
   - `python -m pytest -q Backend/app/tests/test_api.py -k "users_endpoints_do_not_expand_student_attendance_history or get_all_users_returns_paged_student_profiles"`
2. Login and call:
   - `GET /api/users/`
   - `GET /api/users/me/`
   confirm responses are `200` and `student_profile.attendances` is `[]` in these user payloads.

## 2026-04-18 - Add a dedicated Misamis University large dataset seed workflow

### Purpose

Provide a repeatable backend seed script for generating one heavy school dataset with 15,000 students, 33 events, 1,000,000 attendance rows, sanctions coverage, and preconfigured SSG/SG/ORG governance memberships.

### Main files

- `Backend/app/misamis_university_seeder.py`
- `Backend/seed_misamis_university.py`
- `Backend/app/seeder.py`
- `Backend/app/utils/passwords.py`
- `Backend/docs/BACKEND_LARGE_DATA_SEED_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added a dedicated bulk seed module for a Misamis University dataset instead of overloading the default lightweight seed path
- added CLI support for:
  - dry runs
  - replace-existing school recreation
  - configurable bcrypt rounds
  - configurable batching
- seeded one school-scoped `campus_admin`
- seeded `15,000` student users with randomized names, student IDs, and passwords
- seeded a full governance tree with:
  - `1` SSG unit
  - `5` SG units
  - `15` ORG units
- assigned governance members and permissions directly so SSG, SG, and ORG users are usable immediately after seeding
- seeded `33` completed events with active sanction configs
- generated `1,000,000` attendance rows by combining:
  - one core attendance row per student per event
  - extra duplicate history rows to hit the requested total exactly
- created sanction records for every core absent attendance row and added sanction items per record
- extended the password helper so callers can choose bcrypt rounds explicitly for large seed workloads
- expanded default role seeding to include governance role names:
  - `ssg`
  - `sg`
  - `org`

### Route or schema impact

- no route path changes
- no request or response schema changes
- no database schema changes
- added a new operational seed entry point:
  - `python Backend/seed_misamis_university.py`

### Migration impact

- no new migration required
- requires the existing migrated schema to already be present before running the large seed script
- no new environment variables required

### How to test

1. Run a compile check:
   - `python -m compileall Backend/app/misamis_university_seeder.py Backend/seed_misamis_university.py Backend/app/seeder.py Backend/app/utils/passwords.py`
2. Run a dry run:
   - `python Backend/seed_misamis_university.py --dry-run`
3. Run the seed against a migrated database:
   - `python Backend/seed_misamis_university.py`
4. Verify counts and artifacts:
   - confirm `15,000` student profiles exist for `Misamis University`
   - confirm `33` events exist for that school
   - confirm total attendance rows for the seeded school equal `1,000,000`
   - confirm sanction records exist for absent rows
   - confirm the credential CSV and summary JSON were written under `storage/seed_outputs/`

## 2026-04-17 - Speed up bulk import credential preparation and enforce unique per-student temporary passwords

### Purpose

Reduce bulk student import wall-clock time in the worker and guarantee that each imported student receives a distinct random temporary password.

### Main files

- `Backend/app/services/student_import_service.py`
- `Backend/app/tests/test_student_import_email_delivery.py`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- moved import credential attachment to batch preparation instead of hashing each password immediately during row collection
- added batch password hashing with a bounded thread pool so large imports spend less time blocked on serial bcrypt work
- added import-run duplicate protection for generated temporary passwords:
  - each student row now gets a freshly generated password
  - the importer tracks passwords already issued during the current import run
  - if a generated password collides, the importer regenerates before continuing
- kept the existing onboarding email flow aligned with the row-specific temporary password returned from the successful insert batch

### Route or schema impact

- no route path changes
- no request or response schema changes
- runtime behavior change:
  - bulk import workers now prepare unique per-row temporary passwords in batch before insert

### Migration impact

- no database migration required
- no configuration or environment variable changes

### How to test

1. Run focused tests:
   - `python -m pytest -q Backend/app/tests/test_student_import_email_delivery.py Backend/app/tests/test_import_repository.py`
2. Manual bulk import smoke:
   - preview and import a file with at least two new student rows
   - confirm the created students do not share the same temporary password
   - confirm onboarding emails or captured queued task arguments show different passwords per student
3. Performance sanity check:
   - run a larger import batch than the previous repro case
   - confirm the worker spends less time in credential preparation than the prior serial hashing behavior

## 2026-04-17 - Add student login access reporting to campus admin school reports

### Purpose

Let campus admins see which students have successfully signed in and which students still have no successful login history from the existing reports dashboard.

### Main files

- `Backend/app/reports/school/service.py`
- `Backend/app/reports/school/queries.py`
- `Backend/app/tests/test_school_reports.py`
- `Backend/docs/BACKEND_REPORTS_MODULE_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- extended `GET /api/attendance/summary` to include a school-scoped student login access block alongside the existing attendance totals
- added `student_login_summary` with:
  - `total_students`
  - `logged_in_students`
  - `not_logged_in_students`
  - `login_coverage_rate`
- added `student_login_rows` so campus admin dashboards can render a detailed roster-level access report with:
  - student identity/scope fields
  - `has_logged_in`
  - `successful_login_count`
  - `last_login_at`
- applied the same school/department/program scope to the login report and used the summary route's `start_date` and `end_date` window for successful login history counts
- added backend regression coverage for the new summary payload and date-window behavior

### Route or schema impact

- no route path changes
- `GET /api/attendance/summary` response now includes additional compatible top-level fields:
  - `student_login_summary`
  - `student_login_rows`

### Migration impact

- no database migration required
- no configuration or environment variable changes

### How to test

1. Run focused backend tests:
   - `python -m pytest -q Backend/app/tests/test_school_reports.py Backend/app/tests/test_attendance_schemas.py`
2. Run a compile check:
   - `python -m compileall Backend/app/reports/school`
3. Manual smoke:
   - log in as a campus admin
   - open the reports dashboard school summary view
   - confirm the student login report shows logged-in vs not-yet-logged-in counts and a roster table
   - apply a date filter and confirm the login report updates to reflect successful logins inside the selected window

## 2026-04-17 - Extend student attendance overview rows for advanced report dashboards

### Purpose

Support the new recommended attendance report catalog UI with exact student-level status counts from the existing overview endpoint instead of frontend-only estimates.

### Main files

- `Backend/app/schemas/attendance.py`
- `Backend/app/reports/student/service.py`
- `Backend/app/tests/test_attendance_schemas.py`
- `Backend/docs/BACKEND_REPORTS_MODULE_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- extended `StudentListItem` with additional per-student counters:
  - `attended_events`
  - `late_events`
  - `incomplete_events`
  - `absent_events`
  - `excused_events`
- updated `get_students_attendance_overview` to compute these counters from the same attendance rows already used for overview totals/rates
- centralized per-student attendance counting in `app.reports.student.service._summarize_attendances(...)`
- reused the same summary helper inside `get_student_attendance_report` so overview/report counters follow the same display-status logic

### Route or schema impact

- no route path changes
- `GET /api/attendance/students/overview` now returns additional optional-compatible fields per row:
  - `attended_events`
  - `late_events`
  - `incomplete_events`
  - `absent_events`
  - `excused_events`

### Migration impact

- no database migration required
- no configuration or environment variable changes

### How to test

1. Run focused backend schema checks:
   - `python -m pytest -q Backend/app/tests/test_attendance_schemas.py`
2. Call `GET /api/attendance/students/overview` with an authenticated report-capable account and confirm each row now includes the added count fields.
3. Open the reports dashboard and verify advanced student ranking/intervention views can render exact absent/late/incomplete totals without extra per-student fetches.

## 2026-04-17 - Limit InsightFace startup module load to detection and recognition

### Purpose

Reduce InsightFace startup memory pressure on constrained deployments by loading only the modules required for face detection and embedding generation.

### Main files

- `Backend/app/services/face_engine/insightface_adapter.py`
- `Backend/docs/BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added explicit `allowed_modules=("detection", "recognition")` in the InsightFace adapter runtime construction path
- runtime model construction now uses a small compatibility wrapper:
  - tries `FaceAnalysis(..., allowed_modules=[...])`
  - falls back to default constructor if the installed InsightFace version does not support `allowed_modules`
- startup/init logs now include which module-set target is being used

### Route or schema impact

- no route path changes
- no response schema changes

### Migration impact

- no database migration required
- no provider/GPU changes; runtime remains CPU-only
- operationally, this lowers startup model-loading footprint before warm-up

### How to test

1. Run focused tests:
   - `python -m pytest -q Backend/app/tests/test_face_engines.py`
2. Deploy backend and inspect logs during runtime initialization:
   - confirm InsightFace model construction starts with `allowed_modules=detection,recognition`
   - verify runtime reaches stable state instead of repeated cold-restart loops during model load.

## 2026-04-17 - Add explicit InsightFace warm-up inference and startup timing metrics

### Purpose

Reduce cold-start ambiguity by explicitly warming the InsightFace pipeline during initialization and exposing precise startup timing data in runtime status/readiness surfaces.

### Main files

- `Backend/app/services/face_engine/insightface_adapter.py`
- `Backend/app/services/face_recognition.py`
- `Backend/app/routers/security_center.py`
- `Backend/app/schemas/face_recognition.py`
- `Backend/app/tests/test_face_engines.py`
- `Backend/docs/BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added explicit warm-up inference stage after `FaceAnalysis(...)` construction and `prepare(...)`
- warm-up now uses a safe dummy RGB frame and runs `face_analysis.get(...)` so startup primes the same inference entrypoint used by real face registration/detection
- runtime now transitions to `ready` only after warm-up inference succeeds
- captured and logged timing metrics:
  - model construction time
  - `prepare(...)` time
  - warm-up inference time
  - total initialization time
- extended shared runtime state/status payload with timing metrics:
  - `model_construction_duration_ms`
  - `prepare_duration_ms`
  - `warmup_duration_ms`
  - `init_duration_ms`
- warm-up failures now set explicit failed reason `insightface_warmup_failed` (with `last_error`) and keep structured runtime failure responses

### Route or schema impact

- no route path changes
- `GET /api/auth/security/face-status` response now includes optional runtime timing fields:
  - `face_runtime_model_construction_duration_ms`
  - `face_runtime_prepare_duration_ms`
  - `face_runtime_warmup_duration_ms`
  - `face_runtime_init_duration_ms`
- existing `GET /health` and `GET /health/readiness` runtime payloads now include timing metrics through `face_runtime`

### Migration impact

- no database migrations required
- no GPU/provider changes; runtime remains CPU-only (`CPUExecutionProvider`)

### How to test

1. Run focused tests:
   - `python -m pytest -q Backend/app/tests/test_face_engines.py`
2. Start backend and verify logs include model construction, prepare, warm-up, and total init timings.
3. Call:
   - `GET /health`
   - `GET /health/readiness`
   - `GET /api/auth/security/face-status`
   and confirm runtime state/reason and duration fields are populated after successful startup warm-up.

## 2026-04-17 - Refactor InsightFace runtime lifecycle into explicit stateful readiness flow

### Purpose

Remove ambiguous request-time runtime initialization behavior and replace it with explicit InsightFace runtime lifecycle management, structured status reporting, and readiness coverage.

### Main files

- `Backend/app/services/face_engine/insightface_adapter.py`
- `Backend/app/services/face_engine/base.py`
- `Backend/app/services/face_engine/factory.py`
- `Backend/app/services/face_recognition.py`
- `Backend/app/main.py`
- `Backend/app/routers/face_recognition.py`
- `Backend/app/routers/public_attendance.py`
- `Backend/app/routers/security_center.py`
- `Backend/app/routers/health.py`
- `Backend/app/schemas/face_recognition.py`
- `Backend/app/tests/test_face_engines.py`
- `Backend/app/tests/test_routes_face.py`
- `Backend/app/tests/test_public_attendance.py`
- `Backend/app/tests/test_api.py`
- `Backend/docs/BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added explicit InsightFace runtime state machine in shared adapter runtime:
  - `initializing`
  - `ready`
  - `failed`
- added tracked lifecycle metadata:
  - `initialized_at`
  - `last_error`
  - `warmup_started_at`
  - `warmup_finished_at`
- centralized runtime lifecycle responsibilities in `insightface_adapter.py`:
  - config/construction
  - initialization request + execution
  - state/status payload reporting
  - inference access with structured readiness failure
- added explicit runtime initialization entrypoint:
  - `FaceRecognitionService.initialize_face_runtime(...)`
  - startup now calls this intentionally (`trigger="startup"`) instead of probing runtime status through request-style side effects
- removed request-time lazy startup behavior from inference access:
  - request handlers now consume runtime state
  - routes return structured `503` details when runtime is `initializing` or `failed`
- expanded face runtime status surface (service + security route payload usage):
  - `state`
  - `ready`
  - `reason`
  - `last_error`
  - `provider_target`
  - `mode`
  - lifecycle timestamps
- added health/readiness face-runtime signal:
  - `GET /health` now includes `face_runtime` and `readiness`
  - new `GET /health/readiness` returns readiness-oriented status code/body
- added concise transition logging:
  - initialization requested
  - initialization started
  - runtime ready
  - runtime failed

### Route or schema impact

- updated route behavior:
  - `POST /api/face/register`
  - `POST /api/face/register-upload`
  - `POST /api/face/verify`
  - `POST /api/face/face-scan-with-recognition`
  - `POST /public-attendance/events/{event_id}/multi-face-scan`
  - `POST /api/auth/security/face-liveness`
  - `POST /api/auth/security/face-reference`
  - `POST /api/auth/security/face-verify`
  now fail fast with structured runtime state when InsightFace is not ready
- updated `GET /api/auth/security/face-status` response with additional runtime lifecycle fields:
  - `face_runtime_state`
  - `face_runtime_last_error`
  - `face_runtime_provider_target`
  - `face_runtime_mode`
  - `face_runtime_initialized_at`
  - `face_runtime_warmup_started_at`
  - `face_runtime_warmup_finished_at`
- health endpoints:
  - existing `GET /health` payload expanded with `face_runtime` + `readiness`
  - added `GET /health/readiness`

### Migration impact

- no database migrations required
- no GPU/provider configuration changes (runtime remains CPU-safe with `CPUExecutionProvider`)
- existing `FACE_WARMUP_ON_STARTUP` behavior is preserved, but startup now explicitly requests runtime initialization through lifecycle API when enabled

### How to test

1. Run focused tests:
   - `python -m pytest -q Backend/app/tests/test_face_engines.py`
   - `python -m pytest -q Backend/app/tests/test_routes_face.py`
   - `python -m pytest -q Backend/app/tests/test_public_attendance.py`
   - `python -m pytest -q Backend/app/tests/test_api.py -k "health_endpoint_reports_pool_status or health_readiness_endpoint_reports_not_ready_when_face_runtime_initializing or face_pending_user_can_check_face_status_before_password_change"`
2. Verify startup logs include runtime initialization lifecycle transitions.
3. Verify `GET /health` and `GET /health/readiness` clearly report DB and face runtime readiness states.

## 2026-04-17 - Add Railway-friendly backend runtime supervisor and use `alembic upgrade heads`

### Purpose

Make the backend deployable on constrained Railway plans by allowing one backend service to run web, Celery worker, Celery beat, migrations, and seeding together at startup.

### Main files

- `Backend/scripts/run-service.sh`
- `Backend/scripts/run_runtime_stack.py`
- `Backend/docs/BACKEND_RAILWAY_DEPLOYMENT_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- changed web startup to execute a Python runtime supervisor script instead of starting only `uvicorn`
- added optional startup steps driven by environment variables:
  - `RUN_MIGRATIONS_ON_START`
  - `RUN_SEED_ON_START`
  - `RUN_CELERY_WORKER`
  - `RUN_CELERY_BEAT`
- constrained Celery worker startup for small-platform deployments with:
  - `CELERY_WORKER_POOL` (recommended `solo`)
  - `CELERY_WORKER_CONCURRENCY` (recommended `1`)
- added optional `FACE_WARMUP_ON_STARTUP` configuration so constrained deployments can skip InsightFace warm-up during API startup
- added process supervision so the backend service can launch:
  - `uvicorn`
  - Celery worker
  - Celery beat
- changed migration execution from `alembic upgrade head` to `alembic upgrade heads`
  - required because the repository currently contains multiple Alembic heads
- kept explicit single-purpose modes available:
  - `SERVICE_MODE=worker`
  - `SERVICE_MODE=beat`
  - `SERVICE_MODE=migrate`

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - one backend service can now handle API + async sidecars + startup database initialization

### Migration impact

- no new database migrations added
- operational migration command changed:
  - use `alembic upgrade heads`
- new runtime configuration supported:
  - `RUN_MIGRATIONS_ON_START`
  - `RUN_SEED_ON_START`
  - `RUN_CELERY_WORKER`
  - `RUN_CELERY_BEAT`
  - `CELERY_WORKER_POOL`
  - `CELERY_WORKER_CONCURRENCY`
  - `FACE_WARMUP_ON_STARTUP`

### How to test

1. Run `python -m compileall Backend/scripts/run_runtime_stack.py`.
2. Start the backend with:
   - `SERVICE_MODE=web`
   - `RUN_MIGRATIONS_ON_START=true`
   - `RUN_SEED_ON_START=true`
   - `RUN_CELERY_WORKER=true`
   - `RUN_CELERY_BEAT=true`
3. Confirm startup completes and logs show migrations, seeding, Celery, and `uvicorn`.

## 2026-04-17 - Stop forcing local Mailpit SMTP overrides so deployments can use Gmail transport

### Purpose

Align container runtime email behavior with cloud deployment needs by removing hardcoded local SMTP overrides that pinned backend services to Mailpit.

### Main files

- `docker-compose.yml`
- `Backend/docs/BACKEND_EMAIL_LOCAL_TESTING_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- removed `backend`, `worker`, and `beat` hardcoded mail overrides:
  - `EMAIL_TRANSPORT=smtp`
  - `SMTP_HOST=mailpit`
  - `SMTP_PORT=1025`
  - `SMTP_USE_TLS=false`
  - `SMTP_USE_STARTTLS=false`
- added environment-driven transport defaults in local Compose:
  - `EMAIL_TRANSPORT=${EMAIL_TRANSPORT:-gmail_api}`
  - `EMAIL_TIMEOUT_SECONDS=${EMAIL_TIMEOUT_SECONDS:-20}`
- removed `mailpit` as a required dependency for `backend`, `worker`, and `beat`
- updated email guide to document:
  - Gmail API cloud configuration
  - optional Mailpit local testing workflow

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - backend containers now use environment-configured Gmail transport by default instead of forced Mailpit SMTP

### Migration impact

- no database migrations required
- deployment/runtime configuration impact:
  - cloud stacks can use Gmail transport without local Compose SMTP override conflicts
  - Mailpit remains optional for local testing when `EMAIL_TRANSPORT=smtp` and `SMTP_HOST=mailpit`

### How to test

1. Run `docker compose config` and confirm `backend`, `worker`, and `beat` no longer include hardcoded `SMTP_HOST=mailpit`.
2. For Gmail:
   - set Gmail OAuth env vars and `EMAIL_TRANSPORT=gmail_api`
   - run `python Backend/scripts/send_test_email.py --recipient <your-email>`
3. For Mailpit local test:
   - set `EMAIL_TRANSPORT=smtp`, `SMTP_HOST=mailpit`, `SMTP_PORT=1025`
   - run `docker compose up -d --build backend worker beat mailpit`
   - verify message in `http://localhost:8025`

## 2026-04-17 - Restore privileged face-scan MFA, add account-level app preferences, and support remember-me session extension

### Purpose

Re-enable face-scan MFA for privileged users (`admin`, `campus_admin`), add a first-class backend store for cross-device app preferences, and let login callers request longer-lived sessions with `remember_me`.

### Main files

- `Backend/app/core/security.py`
- `Backend/app/models/platform_features.py`
- `Backend/app/models/__init__.py`
- `Backend/app/routers/auth.py`
- `Backend/app/routers/security_center.py`
- `Backend/app/routers/users/__init__.py`
- `Backend/app/routers/users/preferences.py`
- `Backend/app/schemas/auth.py`
- `Backend/app/schemas/user_preference.py`
- `Backend/app/services/auth_session.py`
- `Backend/app/services/user_preference_service.py`
- `Backend/alembic/versions/a4f1b2c3d4e5_add_user_app_preferences.py`
- `Backend/app/tests/test_api.py`
- `Backend/docs/BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md`
- `Backend/docs/BACKEND_USER_PREFERENCES_AND_AUTH_SESSION_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- restored privileged login gating with face-scan MFA:
  - `admin` and `campus_admin` logins now check `user_security_settings.mfa_enabled`
  - MFA-enabled privileged users receive a face-pending token payload instead of an immediate full-access session
  - no `UserSession` row is created until face verification succeeds
- updated `/api/auth/security/face-status` to report `face_verification_required` from the stored security setting instead of only enrollment state
- updated `/api/auth/security/face-verify` so a successful verification upgrades the face-pending token into a full-access session while preserving the requested session lifetime
- added `user_app_preferences` model and service defaults for:
  - `dark_mode_enabled`
  - `font_size_percent`
- added user app preference routes under `/api/users/preferences/me`
- added login `remember_me` handling:
  - `POST /token`
  - `POST /login`
  - requested long-lived sessions now use `user_security_settings.trusted_device_days` (default `14`)
- added API tests for:
  - privileged login returning face-pending tokens
  - remember-me session duration persistence
  - user app preference creation/update

### Route or schema impact

- updated request schemas:
  - `POST /token` accepts form field `remember_me`
  - `POST /login` accepts JSON field `remember_me`
- updated token payload schema/claims:
  - login responses can now return `face_verification_required=true`
  - login responses can now return `face_verification_pending=true`
  - internal token claims now carry `session_duration_minutes`
- new routes:
  - `GET /api/users/preferences/me`
  - `PUT /api/users/preferences/me`
- runtime behavior changes:
  - privileged MFA-enabled logins no longer receive a direct bearer session immediately
  - cross-device app preferences are now stored server-side for authenticated users

### Migration impact

- requires migration:
  - `Backend/alembic/versions/a4f1b2c3d4e5_add_user_app_preferences.py`
- adds table:
  - `user_app_preferences`
- no new environment variables required
- existing `user_security_settings` rows are now active again for:
  - `mfa_enabled`
  - `trusted_device_days`

### How to test

1. Apply migrations:
   - `alembic upgrade head`
2. Run focused backend tests:
   - `python -m pytest -q Backend/app/tests/test_api.py`
3. Manual auth checks:
   - login as `campus_admin` or `admin`
   - confirm login returns `face_verification_required=true`, `face_verification_pending=true`, and `session_id=null`
   - complete `POST /api/auth/security/face-verify`
   - confirm the response returns a full `access_token` and non-null `session_id`
4. Manual remember-me check:
   - call `POST /token` with `remember_me=true`
   - confirm the created session expiry reflects the configured trusted-device window
5. Manual preferences check:
   - call `GET /api/users/preferences/me`
   - call `PUT /api/users/preferences/me` with `dark_mode_enabled` and `font_size_percent`
   - sign in on another device and confirm the saved app preferences are returned by the same route

## 2026-04-16 - Restore platform-admin access for sanctions dashboard and school settings when admin has `school_id = NULL`

### Purpose

Fix `403` regressions for platform admins on sanctions and school-settings flows by preserving true platform-admin identity (`admin` + `school_id = NULL`) while resolving a default school context where school-scoped data is required.

### Main files

- `Backend/app/core/security.py`
- `Backend/app/services/sanctions_service.py`
- `Backend/app/routers/school_settings.py`
- `Backend/app/seeder.py`
- `Backend/app/tests/test_sanctions_api.py`
- `Backend/app/tests/test_api.py`
- `Backend/docs/BACKEND_SANCTIONS_MANAGEMENT_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- added `get_school_id_with_admin_fallback(db, user)` in security core:
  - returns `user.school_id` for school-scoped users
  - for platform `admin` with `school_id = NULL`, resolves default school by lowest `School.id`
  - keeps `403` for non-admin users without school assignment
- updated sanctions service to use admin fallback school resolution for all school-scoped sanctions operations (dashboard, config, list, approve, detail, export, delegation, and clearance deadline flows)
- updated school-settings router `_resolve_current_school(...)` to use the same admin fallback helper
- updated seeder admin bootstrap behavior:
  - new admin rows are created with `school_id = None`
  - removed unused `_apply_admin_defaults(..., default_school_id)` parameter

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - platform admin users with `school_id = NULL` can now access:
    - `GET /api/sanctions/dashboard`
    - `GET /school-settings/me`
  - school-scoped users keep existing assignment checks

### Migration impact

- no database migrations required
- no environment/configuration changes required
- data hygiene note:
  - admin rows should remain `school_id = NULL` for platform-admin semantics

### How to test

1. Run `python -m pytest -q Backend/app/tests/test_sanctions_api.py Backend/app/tests/test_api.py`.
2. Login as platform admin (`admin` role, `school_id = NULL`) and call:
   - `GET /api/sanctions/dashboard`
   - `GET /school-settings/me`
3. Confirm both endpoints return `200`.

## 2026-04-16 - Make sanctions route access governance-role scoped (SSG/SG/ORG) across dashboard, students, approve, detail, export, and deadline flows

### Purpose

Ensure sanctions access is primarily based on active student governance scope ownership/delegation, not only explicit sanctions member-permission grants, so governance officers can use sanctions UI/routes in scoped events.

### Main files

- `Backend/app/routers/sanctions.py`
- `Backend/app/tests/test_sanctions_api.py`
- `Backend/docs/BACKEND_SANCTIONS_MANAGEMENT_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- updated `_ensure_sanctions_permission(...)` to resolve governance role fallback from active governance memberships (`SSG`/`SG`/`ORG` unit types) before enforcing explicit permission-code checks
- retained legacy role-name compatibility fallback for `student_council` and `student council`
- enabled governance-role fallback on additional sanctions routes:
  - `GET /api/sanctions/events/{event_id}/students`
  - `POST /api/sanctions/events/{event_id}/students/{user_id}/approve`
  - `GET /api/sanctions/students/{user_id}`
  - `POST /api/sanctions/clearance-deadline`
  - `GET /api/sanctions/events/{event_id}/export`
- kept service-layer access control unchanged:
  - `_evaluate_event_access(...)` and `_require_event_access(...)` still enforce event scope/delegation/write boundaries

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - governance members can access sanctions routes for scoped events without explicit sanctions permission grants
  - cross-scope access without delegation remains denied by service-level checks

### Migration impact

- no database migrations required
- no environment/configuration changes required

### How to test

1. Run `python -m pytest -q Backend/app/tests/test_sanctions_api.py`.
2. Verify `SG` and `ORG` users with active governance membership (and no explicit sanctions permissions) can access:
   - sanctions students list for owned-scope event
   - sanctions dashboard
   - sanctions export
3. Verify `SG` access to `SSG`-owned event sanctions routes still returns `404` without delegation.

## 2026-04-16 - Relax sanctions dashboard/config guards with manage-events fallback and legacy governance-role fallback

### Purpose

Fix `403` responses on sanctions dashboard/config flows for governance users that already have event-management authority but may not have explicit sanctions-specific permission grants in older setups.

### Main files

- `Backend/app/routers/sanctions.py`
- `Backend/app/tests/test_sanctions_api.py`
- `Backend/docs/BACKEND_SANCTIONS_MANAGEMENT_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- expanded `_ensure_sanctions_permission(...)` with:
  - `fallback_permission_codes`
  - broader governance-role fallback aliases (`student_council`, `student council`) when fallback mode is enabled
- added `manage_events` fallback for sanctions config/delegation routes:
  - `GET /api/sanctions/events/{event_id}/config`
  - `PUT /api/sanctions/events/{event_id}/config`
  - `GET /api/sanctions/events/{event_id}/delegation`
  - `PUT /api/sanctions/events/{event_id}/delegation`
- added dashboard fallback permissions for:
  - `GET /api/sanctions/dashboard`
  - accepts `view_sanctions_dashboard` OR `manage_events` OR `configure_event_sanctions`

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - governance users with `manage_events` can access sanctions config/delegation/dashboard without separate sanctions-dashboard grants
  - legacy governance role naming (`student_council`) is accepted in sanctions role-fallback mode

### Migration impact

- no database migrations required
- no environment/configuration changes required

### How to test

1. Run sanctions API tests:
   - `python -m pytest -q Backend/app/tests/test_sanctions_api.py`
2. Verify a governance member with `manage_events` (without `view_sanctions_dashboard`) can call:
   - `GET /api/sanctions/dashboard`
   - `GET /api/sanctions/events/{event_id}/config`

## 2026-04-16 - Allow SSG/SG/ORG sanctions configuration per scoped event without explicit member permission grants

### Purpose

Ensure governance officers (`SSG`, `SG`, `ORG`) can configure sanctions for events inside their own scope (or delegation scope) even when `configure_event_sanctions` was not explicitly granted at member-permission level.

### Main files

- `Backend/app/routers/sanctions.py`
- `Backend/app/tests/test_sanctions_api.py`
- `Backend/docs/BACKEND_SANCTIONS_MANAGEMENT_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- extended sanctions router permission helper with a governance-role fallback option
- enabled role fallback for:
  - `GET /api/sanctions/events/{event_id}/config`
  - `PUT /api/sanctions/events/{event_id}/config`
  - `GET /api/sanctions/events/{event_id}/delegation`
  - `PUT /api/sanctions/events/{event_id}/delegation`
  - `GET /api/sanctions/dashboard`
- preserved existing guardrails:
  - admin/campus_admin remains fully allowed
  - active governance membership is still required for governance-role fallback
  - service-level event scope and delegation checks still enforce read/write boundaries

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - `SSG`, `SG`, and `ORG` users can now open/manage sanctions config for events they are authorized to access by scope/delegation without requiring explicit member permission grants for `configure_event_sanctions`

### Migration impact

- no database migrations required
- no environment/configuration changes required

### How to test

1. Run sanctions API tests:
   - `python -m pytest -q Backend/app/tests/test_sanctions_api.py`
2. Verify role-scoped access manually:
   - `SSG` can access sanctions config for SSG-owned event
   - `SG` can access sanctions config for SG-owned event
   - `ORG` can access sanctions config for ORG-owned event
   - cross-scope access without delegation remains denied (`404`)
   - non-governance user remains denied (`403`)

## 2026-04-16 - Standardize backend system-name defaults and notification copy to Aura

### Purpose

Align backend-generated messaging with the current product name by replacing remaining `VALID8/Valid8` runtime defaults with `Aura`.

### Main files

- `Backend/app/core/config.py`
- `Backend/app/services/email_service/use_cases.py`
- `Backend/app/services/email_service/transport.py`
- `Backend/app/services/notification_center_service.py`
- `Backend/app/routers/notifications.py`
- `Backend/app/workers/tasks.py`
- `Backend/scripts/send_test_email.py`
- `Backend/scripts/generate_google_oauth_refresh_token.py`
- `.env.example`
- `Backend/docs/EMAIL_FORMATS_EDITABLE.txt`
- `Backend/docs/BACKEND_EMAIL_LOCAL_TESTING_GUIDE.md`
- `Backend/docs/BACKEND_CHANGELOG.md`

### Backend changes

- changed default email sender display name to `Aura Notifications` when `EMAIL_FROM_NAME`/`SMTP_FROM_NAME` are unset
- changed email use-case fallback `system_name` to `Aura` when no school-scoped name is provided
- updated default `/api/notifications/test` subject/body copy to Aura branding
- updated missed/low/reminder notification footers and sanctions-task signatures to `Aura`
- updated email-transport connectivity-test default subject/body/html copy to Aura
- updated operator smoke-test script defaults to Aura wording
- updated OAuth token helper script description text to Aura wording

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - default notification/email text generated by backend now uses `Aura` branding

### Migration impact

- no database migrations required
- configuration default changed:
  - `EMAIL_FROM_NAME` fallback is now `Aura Notifications`

### How to test

1. Run focused backend tests:
   - `python -m pytest -q Backend/app/tests/test_email_service.py Backend/app/tests/test_config.py`
2. Run backend transport smoke test command:
   - `python Backend/scripts/send_test_email.py --recipient test@example.com`
   - verify the default subject starts with `Aura email transport smoke test`
3. Call `POST /api/notifications/test` without a custom `message` and verify the generated default text/subject uses `Aura`.

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

## 2026-04-16 - Seed multi-school demo dataset for assistant role/permission testing

### Purpose

Enable realistic manual testing of the UI + Aura AI assistant across multiple schools, roles, and governance permission codes.

### Main files

- `Backend/app/seeder.py`
- `Backend/app/services/auth_session.py`
- `Backend/docs/BACKEND_DEMO_SEEDING_GUIDE.md`
- `.gitignore`

### Backend changes

- seeder now supports demo seeding (default on) to generate:
  - 5 sample schools
  - 100 sample users (platform admins, campus admins, students)
  - departments/programs per school
  - governance units (SSG/SG/ORG) + governance member permissions for a subset of users
  - demo credentials saved to `Backend/storage/seed_credentials.csv` (gitignored)
- login token issuance now includes:
  - derived governance membership roles in `roles` (`ssg`, `sg`, `org`)
  - governance permission codes in `permissions`
  so the assistant can enforce MCP policy based on the JWT claims.

### Route or schema impact

- no route path changes
- no request/response schema changes
- runtime behavior change:
  - JWT payload now includes a `permissions` claim and may include governance roles (`ssg`/`sg`/`org`) in `roles`

### Migration impact

- no new migrations required

### How to test

1. Run migrations:
   - `python -m alembic upgrade head`
2. Run seeder:
   - `python Backend/seed.py`
3. Open `Backend/storage/seed_credentials.csv` and log in with different users to test assistant behavior.

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

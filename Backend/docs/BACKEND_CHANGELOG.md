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

## 2026-03-13 - Finalize face-recognition naming and normalize attendance payloads

### Purpose

Finished the face-recognition naming cleanup and normalized the event-attendance error payloads without changing the public `/face/...` routes or the success response contract.

### Main files

- `Backend/app/services/event_geolocation.py`
- `Backend/app/services/face_recognition.py`
- `Backend/app/schemas/event.py`
- `Backend/app/schemas/face_recognition.py`
- `Backend/app/models/face_recognition.py`
- `Backend/app/routers/events.py`
- `Backend/app/routers/face_recognition.py`
- `Backend/app/routers/security_center.py`
- `Backend/app/tests/conftest.py`
- `Backend/app/tests/test_api.py`
- `Backend/app/tests/test_models.py`
- `Backend/app/tests/test_event_geolocation_service.py`
- `Frontend/src/api/studentEventCheckInApi.ts`
- `Backend/docs/BACKEND_FACE_GEO_MERGE_GUIDE.md`

### Backend changes

- renamed the student face router module from `app.routers.face` to `app.routers.face_recognition`
- kept the public route prefix and endpoints unchanged at `/face/...`
- added structured error payloads for attendance geolocation failures and required geolocation input failures
- added a message field to attendance travel-risk failures while preserving the existing distance metrics
- included optional `time_status` and `attendance_decision` context in the attendance geolocation response object
- renamed the legacy pytest fixture file to `conftest.py` and switched the backend test harness to a self-contained SQLite setup
- updated the legacy API tests to match the current auth rules and protected-route behavior

### Route or schema impact

- no route paths changed
- no JSON request or response field names changed
- internal router naming is now aligned with the face-recognition service, schema, and model module names
- `POST /events/{event_id}/verify-location` still uses the same request payload and returns the same core geolocation fields
- `POST /face/face-scan-with-recognition` still uses the same request payload and returns the same success fields
- attendance geolocation failure payloads now consistently include `code` and `message` alongside the existing geofence fields

### Migration impact

- no migration required

### Testing

- run `python -m pytest -q`
- smoke-test `GET /`
- smoke-test `POST /events/{event_id}/verify-location` with inside-geofence and outside-geofence coordinates
- smoke-test `POST /face/face-scan-with-recognition` for both success and geolocation/travel-risk failure payloads

## 2026-03-13 - Reduce login latency by moving auth side effects off the request path

### Purpose

Reduced perceived login latency by removing forced SQL query logging and moving login email/notification side effects out of the synchronous request path.

### Main files

- `Backend/app/routers/auth.py`
- `Backend/app/services/auth_background.py`
- `Backend/app/services/email_service.py`
- `Backend/app/services/notification_center_service.py`
- `Backend/app/worker/tasks.py`
- `Backend/app/database.py`
- `Backend/app/tests/test_auth_background.py`
- `Backend/docs/BACKEND_AUTH_LOGIN_PERFORMANCE_GUIDE.md`

### Backend changes

- `/login` now queues account-security notifications asynchronously instead of waiting for SMTP work before responding
- `/login` MFA delivery now validates SMTP configuration first, then dispatches MFA email asynchronously
- `/auth/mfa/verify` now queues the MFA-completed security notification asynchronously
- login-side async dispatch uses Celery first and falls back to FastAPI background tasks if task publishing fails
- SQL query logging is now enabled only when `SQL_ECHO=true`

### Route or schema impact

- no route paths changed
- no login request or response field names changed
- frontend login flow remains compatible

### Migration impact

- no migration required

### Testing

- run `python -m pytest -q`
- smoke-test `POST /login`
- smoke-test `POST /auth/mfa/verify`
- smoke-test frontend production build

## 2026-03-12 - Drop legacy unused database tables

### Purpose

Removed legacy database tables that are no longer used by the active backend models, routers, or services.

### Main files

- `Backend/alembic/versions/9b3e1f2c4d5a_drop_legacy_unused_tables.py`
- `Backend/docs/BACKEND_DATABASE_CLEANUP_GUIDE.md`

### Backend changes

- added a cleanup migration that drops unused legacy tables only when they exist
- preserved all active tables used by current auth, attendance, event, import, notification, security, subscription, and governance flows
- kept the cleanup idempotent by using `DROP TABLE IF EXISTS`

### Route or schema impact

- no HTTP routes changed
- no active request or response schemas changed

### Migration impact

- requires `9b3e1f2c4d5a_drop_legacy_unused_tables.py`
- removes `ai_logs`, `anomaly_logs`, `attendance_predictions`, `event_consumption_logs`, `event_flags`, `event_predictions`, `model_metadata`, `notifications`, `outbox_events`, `recommendation_cache`, `security_alerts`, and `student_risk_scores`

### Testing

- run `alembic upgrade head` on the target PostgreSQL database
- verify the removed tables no longer appear in `information_schema.tables`
- smoke-test login, attendance, events, notifications, security center, governance, and bulk import flows

## 2026-03-11 - Celery Beat automatic event status scheduling

### Purpose

Extended automatic event workflow status sync so it runs even without user traffic, using Celery Beat plus the existing worker and Redis setup.

### Main files

- `Backend/app/core/config.py`
- `Backend/app/services/event_workflow_status.py`
- `Backend/app/worker/celery_app.py`
- `Backend/app/worker/tasks.py`
- `Backend/app/tests/test_event_workflow_status.py`
- `Backend/docs/BACKEND_EVENT_AUTO_STATUS_GUIDE.md`
- `Backend/docs/BACKEND_EVENT_TIME_STATUS_GUIDE.md`
- `docker-compose.yml`

### Backend changes

- added scheduler settings for event auto-status sync enable/interval
- added a periodic Celery task that scans active events and syncs their workflow status
- added summary reporting for scheduler runs so logs show transitions and attendance finalization counts
- added a dedicated Docker `beat` service for local and container deployments
- kept the request-driven route sync as a fallback for resiliency

### Route or task impact

- new scheduled task: `app.worker.tasks.sync_event_workflow_statuses`
- no new HTTP routes were required

### Migration impact

- no migration required

## 2026-03-11 - Automatic event workflow status sync

### Purpose

Added automatic backend syncing of stored event workflow status based on event schedule time, while preserving the existing computed attendance-window status system.

### Main files

- `Backend/app/services/event_workflow_status.py`
- `Backend/app/routers/events.py`
- `Backend/app/routers/attendance.py`
- `Backend/app/routers/face_recognition.py`
- `Backend/app/tests/test_event_workflow_status.py`
- `Backend/docs/BACKEND_EVENT_AUTO_STATUS_GUIDE.md`
- `Backend/docs/BACKEND_EVENT_TIME_STATUS_GUIDE.md`

### Backend changes

- added a reusable service that maps computed time status into stored workflow status
- synced event `status` automatically on relevant event, attendance, and face routes
- preserved `cancelled` as a manual terminal state
- treated `completed` as sticky during automatic sync to avoid accidental reopening
- auto-finalized attendance when time-driven sync moved an event into `completed`

### Route impact

- event list/detail routes now refresh stale workflow status before returning data
- attendance and face attendance helpers now refresh stale workflow status before attendance checks
- no new API routes were required

### Migration impact

- no migration required

## 2026-03-11 - Add `late` attendance status support

### Purpose

Added `late` as a valid attendance status across the backend and database without replacing the repo's current attendance, reporting, face-scan, or event logic.

### Main files

- `Backend/app/models/attendance.py`
- `Backend/app/schemas/attendance.py`
- `Backend/app/services/attendance_status.py`
- `Backend/app/routers/attendance.py`
- `Backend/app/services/notification_center_service.py`
- `Backend/alembic/versions/a12b34c56d78_add_late_to_attendance_status_enum.py`
- `Backend/app/tests/test_attendance_status_support.py`
- `Backend/docs/BACKEND_ATTENDANCE_STATUS_GUIDE.md`

### Backend changes

- added `late` to the SQLAlchemy and Pydantic attendance enums
- added a safe PostgreSQL enum migration using `ADD VALUE IF NOT EXISTS`
- updated reports and summaries so `late` counts as attended
- updated status-count dictionaries so `late` is included and does not cause missing-key errors
- left automatic late-threshold assignment out because this repo does not already have that feature

### Migration impact

- requires `a12b34c56d78_add_late_to_attendance_status_enum.py`

## 2026-03-11 - Event late threshold and automatic absent finalization

### Purpose

Added an event-level late-threshold field and automatic absent materialization when an event is completed.

### Main files

- `Backend/app/models/event.py`
- `Backend/app/schemas/event.py`
- `Backend/app/services/attendance_status.py`
- `Backend/app/services/event_attendance_service.py`
- `Backend/app/routers/events.py`
- `Backend/app/routers/attendance.py`
- `Backend/app/routers/face_recognition.py`
- `Backend/alembic/versions/b45c67d89e01_add_event_late_threshold_minutes.py`

### Backend changes

- events now store `late_threshold_minutes`
- student sign-ins can finalize as `late` when the time-in exceeds the event threshold
- when an event becomes `completed`, the backend auto-creates `absent` records for scoped students with no attendance
- active attendances with no `time_out` are also auto-marked `absent` on event completion

### Migration impact

- requires `b45c67d89e01_add_event_late_threshold_minutes.py`

## 2026-03-11 - Face recognition and geolocation merge from `GITHUB`

### Purpose

Merged the reference face recognition and event geolocation logic from `GITHUB/Backend` into the live `RIZAL_v1` backend.

### Main files

- `Backend/app/services/face_recognition.py`
- `Backend/app/services/auth_session.py`
- `Backend/app/routers/auth.py`
- `Backend/app/routers/security_center.py`
- `Backend/app/routers/face_recognition.py`
- `Backend/app/routers/events.py`
- `Backend/app/models/platform_features.py`
- `Backend/app/models/event.py`
- `Backend/app/models/attendance.py`
- `Backend/alembic/versions/f8b2c1d4e6a7_add_face_profiles_and_event_geo_fields.py`

### Backend changes

- added privileged-user face profiles
- added pending face verification sessions for `admin` and `school_IT`
- added anti-spoof backed privileged face enrollment and verification routes
- added event geofence fields and location verification route
- added combined student face plus geofence attendance scanning

### Important routes

- `POST /auth/login`
- `GET /auth/security/face-status`
- `POST /auth/security/face-liveness`
- `POST /auth/security/face-reference`
- `POST /auth/security/face-verify`
- `POST /face/register`
- `POST /face/register-upload`
- `POST /face/verify`
- `POST /face/face-scan-with-recognition`
- `POST /events/{event_id}/verify-location`

### Migration impact

- requires `f8b2c1d4e6a7_add_face_profiles_and_event_geo_fields.py`

## 2026-03-11 - Geolocation validation hardening

### Purpose

Improved geofence decision safety and reason codes for student attendance and event location verification.

### Main files

- `Backend/app/services/geolocation.py`
- `Backend/app/tests/test_geolocation.py`

### Backend changes

- added coordinate validation helpers
- added radius validation helpers
- added safer accuracy normalization
- added stable location reason codes
- added optional buffered geofence decision mode
- added recommended GPS accuracy helper

### Configuration impact

- no database migration required

## 2026-03-11 - Attendance sign-in/sign-out completion logic

### Purpose

Made attendance status depend on both sign-in and sign-out completion, aligned with the event schedule.

### Main files

- `Backend/app/routers/face_recognition.py`
- `Backend/app/routers/attendance.py`

### Backend changes

- sign-in now creates a provisional attendance record
- sign-out finalizes the attendance record
- final status becomes `present` only when the recorded attendance window aligns with the event schedule
- unfinished attendance cleanup was adjusted to preserve correct processing

### Route impact

- behavior changed in `POST /face/face-scan-with-recognition`

## 2026-03-11 - Dynamic event time status for attendance decisions

### Purpose

Added a computed event time-status layer so attendance windows can be enforced automatically from event schedule data without writing a second status to the database.

### Main files

- `Backend/app/services/event_time_status.py`
- `Backend/app/services/attendance_status.py`
- `Backend/app/routers/events.py`
- `Backend/app/routers/face_recognition.py`
- `Backend/app/routers/attendance.py`
- `Backend/app/tests/test_event_time_status.py`
- `Backend/app/tests/test_attendance_status_support.py`
- `Backend/docs/BACKEND_EVENT_TIME_STATUS_GUIDE.md`

### Backend changes

- added `get_event_status()` for computed `upcoming/open/late/closed` event windows
- added `get_attendance_decision()` for `present/late/reject` attendance decisions
- exposed `GET /events/{event_id}/time-status`
- extended `POST /events/{event_id}/verify-location` to include dynamic time-status and attendance-decision payloads
- enforced automatic `upcoming` and `closed` rejection for new student and staff attendance check-ins
- normalized event schedule and attendance timestamps more safely for `Asia/Manila`

### Migration impact

- no database migration required

## 2026-03-11 - Login guard for invalid school and admin account state

### Purpose

Stopped invalid accounts from logging in and then failing later with misleading school-context errors.

### Main files

- `Backend/app/services/auth_session.py`
- `Backend/app/routers/auth.py`
- `Backend/app/tests/test_auth_session_login_guard.py`

### Backend changes

- login now rejects inactive accounts
- login now rejects accounts with no assigned role
- login now rejects school-scoped accounts that are missing a valid school assignment
- login now rejects accounts linked to inactive schools
- MFA verification re-checks the same account-state guard before completing login

### Migration impact

- no database migration required

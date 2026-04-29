# Backend Runtime Behavior

<!--nav-->
[← API Overview](api-overview.md) | [🏠 Home](/README.md) | [Backend Changelog →](BACKEND_CHANGELOG.md)

---
<!--/nav-->

This page documents backend behaviors that affect startup or runtime even if no route contract changed.

## Configuration Source of Truth

- Environment variables now cover secrets, connection strings, and deployment URLs only.
- Non-secret backend runtime defaults now live in `backend/app/core/app_settings.py`.
- Backend env parsing remains in `backend/app/core/config.py`.

This includes:

- import limits and storage defaults
- school-logo storage defaults
- API rate limits, request body limits, trusted host defaults, and API docs exposure
- face, liveness, geolocation, and public-attendance thresholds
- event sync timing
- email timeout and startup verification defaults

## List Pagination And Read-Only GETs

List routes that can grow large now return a shared paginated envelope with `data`, `page`, `total`, `total_pages`, `limit`, `next`, and `prev`.

Affected routes:

- `GET /api/events/`
- `GET /api/events/ongoing`
- `GET /api/users/`
- `GET /api/users/by-role/{role_name}`
- `GET /api/governance/students`

Runtime behavior:

- clients pass `page` and `limit`; backend limits enforce safe maximum page sizes.
- event list, event detail, event attendees, and event stats GET routes no longer persist event workflow status sync side effects.
- attendance event-report GET no longer commits event workflow sync side effects before report generation.
- completed-event attendance finalization no longer creates absent attendance rows for students who never signed in; those absences are computed from the event participant scope and real attendance rows.

How to test:

1. Run `python -m compileall Backend/app`.
2. Call the affected routes with `page=1&limit=1` and confirm the response has a `data` array plus pagination metadata.
3. Compare attendance rows before and after calling `GET /api/events/`, `GET /api/events/{event_id}`, `GET /api/events/{event_id}/attendees`, `GET /api/events/{event_id}/stats`, and `GET /api/attendance/events/{event_id}/report`; row counts should not change.
4. For a completed event with participants who never signed in, verify no new attendance rows are created by finalization and report absentees are computed from participants minus real valid attendance rows.

## Anti-Abuse and Request Hardening

The API now has shared abuse controls in addition to endpoint-specific validation.

Runtime behavior:

- Redis-backed fixed-window rate limiting is used when Redis is reachable.
- If Redis is unavailable and `RATE_LIMIT_FAIL_OPEN=true`, the backend falls back to an in-process limiter so local/dev environments continue working.
- Login and forgot-password endpoints have stricter per-IP/email limits.
- Mutating requests have a broad bearer-token/IP limiter.
- Face recognition, public attendance, and health endpoints have route-level limits because they are public or CPU-sensitive.
- Oversized requests with a `Content-Length` above `MAX_REQUEST_BODY_SIZE_MB` are rejected with `413`.
- Face image uploads reject non-image content types, empty files, and files larger than `FACE_IMAGE_MAX_SIZE_MB`.
- `TRUSTED_HOSTS` enables `TrustedHostMiddleware` when set to a list other than `*`.
- `API_DOCS_ENABLED=false` disables `/docs`, `/redoc`, and `/openapi.json`.

Relevant configuration:

- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_FAIL_OPEN`
- `RATE_LIMIT_LOGIN_COUNT`
- `RATE_LIMIT_LOGIN_WINDOW_SECONDS`
- `RATE_LIMIT_FORGOT_PASSWORD_COUNT`
- `RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS`
- `RATE_LIMIT_AUTHENTICATED_MUTATION_COUNT`
- `RATE_LIMIT_AUTHENTICATED_MUTATION_WINDOW_SECONDS`
- `RATE_LIMIT_FACE_COUNT`
- `RATE_LIMIT_FACE_WINDOW_SECONDS`
- `RATE_LIMIT_PUBLIC_COUNT`
- `RATE_LIMIT_PUBLIC_WINDOW_SECONDS`
- `MAX_REQUEST_BODY_SIZE_MB`
- `FACE_IMAGE_MAX_SIZE_MB`
- `API_DOCS_ENABLED`
- `TRUSTED_HOSTS`

How to test:

1. Set `RATE_LIMIT_ENABLED=true`, `RATE_LIMIT_LOGIN_COUNT=1`, and `RATE_LIMIT_LOGIN_WINDOW_SECONDS=60`.
2. Submit the same invalid `POST /login` payload twice.
3. Confirm the first response is the normal auth failure and the second response is `429` with `detail.code=rate_limit_exceeded` and a `Retry-After` header.
4. Upload a `text/plain` file to `POST /api/face/register-upload` while authenticated as a student and confirm `415`.
5. Send a request with `Content-Length` above `MAX_REQUEST_BODY_SIZE_MB` and confirm `413`.

## Email Startup Validation

Outbound email is currently disabled in code. API startup logs a warning and does not validate or connect to Mailjet while this code-level switch is disabled.

Supported transports:

- `disabled`
- `mailjet_api`

Behavior:

- password reset, onboarding, and notification email sends are skipped even if `EMAIL_TRANSPORT=mailjet_api` is configured.
- notification email-channel logs use `status=skipped`; in-app notification logs can still be created.
- when code-level email delivery is re-enabled, `disabled` logs a warning and `mailjet_api` validates the canonical sender, Mailjet credentials, and optional connectivity before startup completes.

## Student Default Passwords

Student accounts created by bulk import and the manual Campus Admin student flow use the same default password rule:

- password value is the student's last name, trimmed and lowercased
- if the last name is blank, the fallback password is `password`
- `using_default_import_password=true` allows login and change-password current-password checks to match this default case-insensitively
- once the student changes password, `using_default_import_password=false` and normal password checks are case-sensitive

Forgot-password behavior:

- `POST /auth/forgot-password` keeps the same request body: `{ "email": "student@example.com" }`
- if the email belongs to an active student account, the backend immediately resets the password to the default last-name password
- the reset sets `must_change_password=false` and `should_prompt_password_change=true`, so login can continue while the UI may prompt the student to change the password
- non-students, inactive users, admins, Campus Admins, and unknown emails return the generic response without changing a password
- pending password-reset request rows for that student are marked `auto_reset` and resolved; no approval or email is required

How to test:

1. Create or import a student whose last name is `Santos`.
2. Log in with `SANTOS` and confirm login succeeds while the default-password flag is still active.
3. Change the password to `NewPass1`.
4. Confirm login with `NewPass1` succeeds and login with `NEWPASS1` fails.
5. Submit `POST /auth/forgot-password` for that student email.
6. Confirm login with `santos`, `SANTOS`, or another casing succeeds and the UI receives the password-change recommendation.

## Storage Path Resolution

Relative backend storage directories are resolved from the runtime backend root.

- local repository layout:
  - `backend/app/core/config.py` resolves `storage/imports` to `<repo>/storage/imports`
- Docker layout:
  - `/app/app/core/config.py` resolves `storage/imports` to `/app/storage/imports`

This matters for bulk student imports because the preview manifest and failed-row report must be readable by both the API container and the Celery worker through the shared import storage volume.

## Student Import Rate Limiting

The student import queue is rate-limited per user.

- failed jobs do not count toward the recent-job limit
- jobs that are still pending, processing, or completed inside the active window still count

This keeps retry behavior practical after backend-side import failures while still protecting the queue from repeated rapid submissions.

Relevant files:

- `backend/app/core/config.py`
- `backend/app/services/email_service/config.py`
- `backend/app/services/email_service/transport.py`

Related guide:

- [Email Delivery Guide (Mailjet / Disabled)](./BACKEND_EMAIL_LOCAL_TESTING_GUIDE.md)

## Audit Log Timezone

Audit log timestamps are stored in UTC in the database, but backend audit log responses now normalize them to `Asia/Manila` before returning them to clients.

Affected response paths:

- `GET /api/audit-logs`
- `GET /school-settings/me/audit-logs`

Relevant files:

- `backend/app/core/timezones.py`
- `backend/app/reports/system/service.py`
- `backend/app/schemas/audit.py`
- `backend/app/routers/school_settings.py`

Runtime details:

- `GET /api/audit-logs` keeps the Manila-local `+08:00` response offset produced by the report service instead of coercing it back to `Z` during schema serialization.
- naive audit timestamps from SQLite tests or legacy rows are still treated as UTC before conversion, so responses remain deterministic.

## Attendance Timestamp Storage

Attendance record timestamps are stored as timezone-aware UTC values in PostgreSQL.

Affected database fields:

- `attendances.time_in`
- `attendances.time_out`

Runtime behavior:

- attendance write paths persist aware UTC timestamps instead of naive `datetime.utcnow()` values
- backend attendance serializers continue returning explicit timezone offsets in API payloads
- frontend attendance screens must format these as API timestamps, not as Manila-local event schedule inputs

Relevant files:

- `backend/app/core/timezones.py`
- `backend/app/models/attendance.py`
- `backend/app/routers/attendance/check_in_out.py`
- `backend/app/routers/face_recognition.py`
- `backend/app/routers/public_attendance.py`

## System Timestamp Storage

Common backend audit and system timestamps are now stored as timezone-aware UTC values in PostgreSQL.

Affected areas:

- user and school lifecycle metadata
- governance unit, member, permission, announcement, and note audit fields
- security sessions, login history, password reset requests, and face-verification audit fields
- notification, subscription reminder, privacy-consent, and data-request audit fields
- bulk import job/error/email-delivery timestamps
- sanctions configuration, record, delegation, compliance, and clearance timestamps

Runtime behavior:

- backend model defaults and `onupdate` hooks now use `utc_now()` instead of naive `datetime.utcnow()`
- write paths that explicitly set DB timestamps now persist aware UTC values
- response schemas continue normalizing these values to explicit UTC offsets for API clients
- frontend consumers that already parse ISO datetimes continue to work without Manila-specific guessing

Scope intentionally unchanged:

- event schedule fields such as `events.start_datetime` and `events.end_datetime` keep their existing Manila-local scheduling behavior
- event time-window logic is not changed by this migration

Relevant files:

- `Backend/alembic/versions/d5e6f7a8b9c0_make_common_system_timestamps_timezone_aware.py`
- `backend/app/core/timezones.py`
- `backend/app/models/user.py`
- `backend/app/models/school.py`
- `backend/app/models/platform_features.py`
- `backend/app/models/governance_hierarchy.py`
- `backend/app/models/import_job.py`
- `backend/app/models/password_reset_request.py`
- `backend/app/models/event_type.py`
- `backend/app/models/sanctions.py`
- `backend/app/repositories/import_repository.py`
- `backend/app/routers/auth.py`
- `backend/app/routers/governance.py`
- `backend/app/routers/security_center.py`
- `backend/app/routers/subscription.py`
- `backend/app/services/security_service.py`
- `backend/app/services/notification_center_service.py`
- `backend/app/services/sanctions_service.py`

## Attendance Completion Status

Present and late are final statuses only when an attendance row has both `time_in` and `time_out`.

- `time_in=NULL` and `time_out=NULL` displays as stored `absent` or `excused`
- `time_in` set and `time_out=NULL` displays and counts as `absent`
- `time_in` set and `time_out` set may display as `present` or `late`
- event stats, attendee status filters, student records, and reports share this resolver

Legacy `incomplete_*` response fields may still exist in schemas for compatibility, but no-sign-out rows are not surfaced as final `incomplete` statuses.

Relevant files:

- `backend/app/services/attendance_status.py`
- `backend/app/routers/events/attendance_queries.py`
- `backend/app/routers/attendance/shared.py`
- `backend/app/schemas/attendance.py`

## Face Runtime Warm-Up

On API startup, the backend may trigger the InsightFace warm-up flow.

- This is controlled by `backend/app/core/app_settings.py`, not `.env`.
- Warm-up failures are logged but do not block API startup.

Related guide:

- [Face Engine Migration Guide](./BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md)

## Face Verification Error Messages

Student self-scan attendance and privileged face verification now normalize single-face verification failures into stable user-facing messages.

Affected routes:

- `POST /api/face/face-scan-with-recognition`
- `POST /api/auth/security/face-verify`

Behavior:

- no detectable single face, multiple faces in one frame, encoding failure, or spoof/liveness rejection return `Face not found.`
- a valid single live face that does not match the enrolled reference returns `Face not match.`
- attendance is never recorded when the frame contains multiple faces because the route still requires exactly one face before any attendance write

Relevant files:

- `backend/app/routers/face_recognition.py`
- `backend/app/routers/security_center.py`
- `backend/app/services/face_recognition.py`

## Production Bootstrap Flow

Production data initialization is now limited to a single explicit command:

- `python backend/bootstrap.py ...`

The backend no longer ships demo or bulk seed entrypoints, and it no longer relies on `SEED_*` env toggles to decide what data to create.

## Event Create Idempotency

Event creation now supports an optional idempotency header for duplicate-submit protection.

Affected route:

- `POST /api/events/`

Behavior:

- clients may send `X-Idempotency-Key` when creating an event
- the first request with a new key creates the event normally
- a repeated request with the same key from the same authenticated user returns the already-created event instead of inserting a duplicate row
- omitting the header keeps the existing non-idempotent create behavior

Relevant files:

- `Backend/alembic/versions/e6f7a8b9c0d1_add_event_create_idempotency_fields.py`
- `backend/app/models/event.py`
- `backend/app/routers/events/crud.py`

## Event Type Lookup

Event categorization now uses a dedicated lookup relation instead of a free-text event column.

- `event_types` stores global defaults and future school-specific custom event categories.
- `events.event_type_id` references `event_types.id`.
- `GET /api/events` returns `event_type_id` plus a nested `event_type` object when one is assigned.
- `POST /api/events` and `PATCH /api/events/{event_id}` accept `event_type_id`.
- `PATCH /api/events/{event_id}` also tolerates partial payloads that omit `event_type_id`, so schedule-only updates do not raise compatibility errors.
- student attendance report endpoints still preserve the existing chart payload shape, but now use the related event type name when present and only fall back to `Regular Events` when no type is assigned.

1. In Docker, run `python - <<'PY'\nfrom app.core.config import get_settings\nprint(get_settings().import_storage_dir)\nPY` and confirm it prints `/app/storage/imports`.
2. Start the API and confirm:
   - `EMAIL_TRANSPORT=disabled` allows startup with a warning
   - `EMAIL_TRANSPORT=mailjet_api` fails fast when credentials are incomplete
4. Run `python backend/bootstrap.py --admin-email admin@example.com --admin-password ChangeMe123!` on a clean database and confirm the admin account is created without any demo schools or sample users.
5. Open the audit log endpoints and confirm returned `created_at` values include a `+08:00` offset.
6. Run `python -m alembic upgrade head` and confirm the migration creates `event_types`, adds `events.event_type_id`, and backfills legacy `events.event_type` values if they exist.
7. Open `GET /api/events/` and confirm the endpoint returns `200` plus `event_type_id` / `event_type` fields for typed events.
8. Call `PATCH /api/events/{event_id}` with only `start_datetime` and `end_datetime` and confirm the route returns `200` while still recalculating near-start attendance override fields.
9. Run `python -m alembic upgrade head` again after the timezone migrations and confirm the latest revisions convert attendance plus system timestamps to `TIMESTAMP WITH TIME ZONE`.
10. Check a session, notification, governance, or password-reset API response and confirm returned datetime fields include explicit UTC offsets instead of naive strings.
11. Call `POST /api/events/` twice with the same `X-Idempotency-Key` as the same user and confirm both responses return the same event ID while only one row is stored.

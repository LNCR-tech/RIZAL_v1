# Backend Runtime Behavior

[<- Back to backend index](./README.md)

This page documents backend behaviors that affect startup or runtime even if no route contract changed.

## Configuration Source of Truth

- Environment variables now cover secrets, connection strings, and deployment URLs only.
- Non-secret backend runtime defaults now live in `Backend/app/core/app_settings.py`.
- Backend env parsing remains in `Backend/app/core/config.py`.

This includes:

- import limits and storage defaults
- school-logo storage defaults
- face, liveness, geolocation, and public-attendance thresholds
- event sync timing
- email timeout and startup verification defaults

## Email Startup Validation

On API startup, the backend validates outbound email configuration.

Supported transports:

- `disabled`
- `mailjet_api`

Behavior:

- `disabled` logs a warning and lets the API start.
- `mailjet_api` validates the canonical sender, Mailjet credentials, and optionally verifies connectivity against Mailjet before startup completes.

Relevant files:

- `Backend/app/core/config.py`
- `Backend/app/services/email_service/config.py`
- `Backend/app/services/email_service/transport.py`

Related guide:

- [Email Delivery Guide (Mailjet / Disabled)](./BACKEND_EMAIL_LOCAL_TESTING_GUIDE.md)

## Audit Log Timezone

Audit log timestamps are stored in UTC in the database, but backend audit log responses now normalize them to `Asia/Manila` before returning them to clients.

Affected response paths:

- `GET /api/audit-logs`
- `GET /school-settings/me/audit-logs`

Relevant files:

- `Backend/app/core/timezones.py`
- `Backend/app/reports/system/service.py`
- `Backend/app/routers/school_settings.py`

## Face Runtime Warm-Up

On API startup, the backend may trigger the InsightFace warm-up flow.

- This is controlled by `Backend/app/core/app_settings.py`, not `.env`.
- Warm-up failures are logged but do not block API startup.

Related guide:

- [Face Engine Migration Guide](./BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md)

## Production Bootstrap Flow

Production data initialization is now limited to a single explicit command:

- `python Backend/bootstrap.py ...`

The backend no longer ships demo or bulk seed entrypoints, and it no longer relies on `SEED_*` env toggles to decide what data to create.

## Event Type Removal

`event_type` is no longer part of the backend event model or event create/update flow.

- `GET /api/events` no longer depends on an `events.event_type` database column.
- Student attendance report endpoints keep the existing event-type chart payload shape only for frontend compatibility, using the fixed label `Regular Events`.
- `GET /api/attendance/students/{student_id}/report` no longer supports an `event_type` query filter.

## How to Test

1. Run `pytest Backend/app/tests/test_config.py Backend/app/tests/test_email_service.py Backend/app/tests/test_seeder.py Backend/app/tests/test_audit_log_timezones.py`.
2. Run `pytest Backend/app/tests/test_admin_import_preview_flow.py` to confirm import storage still honors the centralized backend settings object.
3. Start the API and confirm:
   - `EMAIL_TRANSPORT=disabled` allows startup with a warning
   - `EMAIL_TRANSPORT=mailjet_api` fails fast when credentials are incomplete
4. Run `python Backend/bootstrap.py --admin-email admin@example.com --admin-password ChangeMe123!` on a clean database and confirm the admin account is created without any demo schools or sample users.
5. Open the audit log endpoints and confirm returned `created_at` values include a `+08:00` offset.
6. Open `GET /api/events/` against a database that does not have `events.event_type` and confirm the endpoint still returns `200`.

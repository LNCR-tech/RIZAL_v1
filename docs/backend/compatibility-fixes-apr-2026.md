# Backend compatibility fixes (April 2026)

## What changed

- Restored ORM-safe compatibility aliases in models so legacy attribute names keep working in SQLAlchemy queries:
  - `AttendanceRecord`: `status`, `method`, `student_id`, `verified_by`
  - `Event`: `start_datetime`, `end_datetime`, `attendances`
  - `School`: `school_name`, `name`, `active_status`, `settings`
- Updated event create/update mapping to persist status values safely for database writes.
- Updated `/api/auth/security/sessions` response mapping to serialize session UUID ids as strings.
- Fixed notification logging metadata handling by storing metadata entries as `notification_log_attributes` records.
- Restored `/api/audit-logs` backward-compatible list response shape for existing clients/tests.
- Updated subscription fallback creation logic to use the current `school_subscriptions` + `subscription_plans` schema (plan lookup, `plan_id`, `status`, `starts_on`).
- Hardened school/school-settings response builders to provide non-null color/subscription defaults expected by response schemas.
- Updated attendance test fixture event window to be runtime-relative (future start) so near-start validation remains enforced.

## Affected routes and behavior

- `GET /api/auth/security/sessions`: `id` is now always serialized as a JSON string.
- `GET /api/audit-logs`: returns a list payload for compatibility with existing consumers.
- `GET /api/subscription/me` and `PUT /api/subscription/me`:
  - uses plan relationship-backed limits
  - supports plan changes through existing plan codes
  - no longer attempts to write non-existent `SchoolSubscription` fields.
- School branding/settings reads now return safe defaults when branding/subscription values are missing.

## How to test

From `backend/` run:

```bash
pytest tests/test_events.py tests/test_attendance.py tests/test_reports.py tests/test_school.py tests/test_school_settings.py tests/test_security_center.py tests/test_subscription.py tests/test_notifications.py tests/test_audit_logs.py
```

Then run full suite:

```bash
pytest
```

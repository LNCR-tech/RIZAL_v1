# Backend User Preferences And Auth Session Guide

> **Status:** ACTIVE
> **Last Updated:** 2026-04-17

## Purpose

This page summarizes the current backend behavior for:

- privileged face MFA during login
- `remember_me` session lifetime extension
- user-level app preferences stored for cross-device frontend sync

## Scope

The backend now treats two user-scoped persistence areas as part of session and account configuration behavior:

- `user_security_settings`
  - existing table
  - controls whether privileged login requires face verification
  - stores trusted-device session duration in days
- `user_app_preferences`
  - new table
  - stores account-level UI preferences that the frontend can reload on another device

## Data Model Summary

### `user_app_preferences`

Migration:

- `Backend/alembic/versions/a4f1b2c3d4e5_add_user_app_preferences.py`

Columns:

- `user_id`
- `dark_mode_enabled`
- `font_size_percent`
- `updated_at`

Defaults:

- `dark_mode_enabled = false`
- `font_size_percent = 100`

Normalization rules:

- font size is clamped to `80..130`
- font size snaps to `5` percent steps

### `user_security_settings`

Relevant behavior currently used by login:

- `admin` and `campus_admin` default to `mfa_enabled = true`
- `remember_me` uses `trusted_device_days`
- trusted-device days are clamped to `1..90`
- default trusted-device window is `14` days

## Routes

### User app preferences

- `GET /api/users/preferences/me`
- `PUT /api/users/preferences/me`

`GET` behavior:

- creates the row on first access if it does not exist yet

`PUT` behavior:

- updates only provided fields
- re-normalizes font size server-side before persistence

Example `PUT` payload:

```json
{
  "dark_mode_enabled": true,
  "font_size_percent": 125
}
```

### Login and session-related routes

- `POST /token`
- `POST /login`
- `GET /api/auth/security/face-status`
- `POST /api/auth/security/face-reference`
- `POST /api/auth/security/face-verify`

New request field:

- `remember_me`

`/token` accepts it as form data:

```text
remember_me=true
```

## Privileged Face MFA Flow

Privileged roles:

- `admin`
- `campus_admin`

When `mfa_enabled = true` for one of those users:

1. password login succeeds
2. backend returns a face-pending login response
3. no `UserSession` row is created yet
4. frontend must complete face verification
5. a successful face verification upgrades the pending login into a normal authenticated session

Face-pending response characteristics:

- `face_verification_required = true`
- `face_verification_pending = true`
- `session_id = null`
- token claim includes `face_pending = true`

Full session after `POST /api/auth/security/face-verify`:

- returns a new `access_token`
- returns a non-null `session_id`
- creates a persisted `UserSession`
- keeps the session duration requested by the original login, including `remember_me`

## Remember-Me Behavior

Remember-me does not create a new token type. It extends token and session lifetime.

- `remember_me = false`
  - uses normal `ACCESS_TOKEN_EXPIRE_MINUTES`
- `remember_me = true`
  - uses `trusted_device_days * 24 * 60`

This applies to:

- direct full-access login
- privileged face-pending login
- upgraded session issued after face verification

## Cross-device App Configuration Sync

The backend account-level preference store is intended for frontend settings that should follow the user across devices.

Current synchronized fields:

- dark mode
- font size

Still stored separately:

- notification delivery preferences

The frontend settings UI may save both, but they are persisted through different backend models and routes.

## Validation Constants

Current service-level constants:

- `APP_FONT_SIZE_MIN = 80`
- `APP_FONT_SIZE_MAX = 130`
- `APP_FONT_SIZE_STEP = 5`
- `APP_FONT_SIZE_DEFAULT = 100`
- `APP_TRUSTED_DEVICE_DAYS_DEFAULT = 14`
- `APP_TRUSTED_DEVICE_DAYS_MIN = 1`
- `APP_TRUSTED_DEVICE_DAYS_MAX = 90`

## Testing Checklist

### Automated

Run:

```bash
docker compose exec backend python -m pytest app/tests/test_api.py -q
```

Covered scenarios include:

- privileged login returns a face-pending response
- `remember_me` extends session lifetime
- app preference routes create and update `user_app_preferences`

### Manual

1. Apply migrations with `alembic upgrade head`.
2. Login as `campus_admin`.
3. Confirm the response includes `face_verification_required = true`.
4. Confirm `session_id` is `null` before face verification.
5. Complete `POST /api/auth/security/face-verify`.
6. Confirm the response returns a full access token and non-null `session_id`.
7. Login as a non-privileged user with `remember_me = true`.
8. Confirm the resulting expiry reflects the trusted-device duration.
9. Call `GET /api/users/preferences/me`.
10. Call `PUT /api/users/preferences/me` with updated `dark_mode_enabled` and `font_size_percent`.
11. Sign in on another device and confirm the same preference values load from the backend.

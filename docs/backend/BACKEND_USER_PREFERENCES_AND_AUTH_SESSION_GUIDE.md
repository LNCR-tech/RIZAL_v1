[← Back to Main README](../../README.md)

# Backend User Preferences And Auth Session Guide

This guide documents the backend behavior for:

- privileged face-scan MFA during login
- remember-me session lifetime extension
- per-user app preferences stored for cross-device sync

## Scope

The backend now treats two user-scoped persistence areas as part of account session behavior:

- `user_security_settings`
  - existing table
  - controls whether privileged login requires face verification
  - stores trusted-device session duration in days
- `user_app_preferences`
  - new table
  - stores account-level UI preferences that the frontend can re-apply on another device

## Data model

### `user_app_preferences`

Migration:

- `Backend/alembic/versions/a4f1b2c3d4e5_add_user_app_preferences.py`

Columns:

- `user_id`:
  - primary key
  - foreign key to `users.id`
- `dark_mode_enabled`
- `font_size_percent`
- `updated_at`

Defaults:

- `dark_mode_enabled=false`
- `font_size_percent=100`

Normalization rules:

- font size is clamped to `80..130`
- font size snaps to `5` percent steps

### `user_security_settings`

This table already existed, but login now actively uses it again.

Relevant columns:

- `mfa_enabled`
- `trusted_device_days`

Default behavior:

- `admin` and `campus_admin` users default to `mfa_enabled=true`
- remember-me uses `trusted_device_days`
- trusted-device days are clamped to `1..90`
- default trusted-device window is `14` days

## Routes

### User app preferences

Routes:

- `GET /api/users/preferences/me`
- `PUT /api/users/preferences/me`

### User profile payload scope

Routes:

- `GET /api/users/`
- `GET /api/users/me/`
- `GET /api/users/{user_id}`

Behavior:

- `student_profile` in users responses is summary-only (identity and academic scope fields)
- users endpoints do not embed full attendance-history rows
- `student_profile.attendances` is always returned as `[]` on users endpoints
- use attendance/report routes for attendance history:
  - `/api/attendance/*`
  - `/api/reports/*`

Request body for `PUT`:

```json
{
  "dark_mode_enabled": true,
  "font_size_percent": 125
}
```

Response shape:

```json
{
  "user_id": 12,
  "dark_mode_enabled": true,
  "font_size_percent": 125,
  "updated_at": "2026-04-17T12:34:56.000000"
}
```

Behavior:

- `GET` creates the row on first access if it does not exist yet
- `PUT` updates only the provided fields
- font size is normalized server-side before persistence

### Login routes

Routes:

- `POST /token`
- `POST /login`

New request field:

- `remember_me`

Examples:

`/token` form field:

```text
remember_me=true
```

`/login` JSON:

```json
{
  "email": "admin@school.edu",
  "password": "secret",
  "remember_me": true
}
```

## Privileged face MFA flow

Privileged roles:

- `admin`
- `campus_admin`

When `mfa_enabled=true` for one of those users:

1. password login succeeds
2. backend returns a face-pending token response
3. no `UserSession` row is created yet
4. frontend must complete face verification
5. successful face verification upgrades the session into a normal full-access bearer session

Face-pending login response characteristics:

- `face_verification_required=true`
- `face_verification_pending=true`
- `session_id=null`
- access token claim `face_pending=true`

Full session after successful face verification:

- returns a new `access_token`
- returns `session_id`
- creates a persisted `UserSession`
- preserves the requested session duration from the original pending token

Relevant security routes:

- `GET /api/auth/security/face-status`
- `POST /api/auth/security/face-reference`
- `POST /api/auth/security/face-verify`

## Remember-me behavior

Remember-me does not create a different token type. It changes the token and session lifetime.

Behavior:

- `remember_me=false`
  - uses normal `ACCESS_TOKEN_EXPIRE_MINUTES`
- `remember_me=true`
  - uses `user_security_settings.trusted_device_days * 24 * 60`

This applies to:

- direct full-access logins
- privileged face-pending logins
- upgraded sessions issued after `POST /api/auth/security/face-verify`

## Cross-device app configuration sync

The backend account-level preference store is intended for app configuration that should follow the user across devices.

Current synchronized fields:

- dark mode
- font size

Notes:

- notification delivery preferences remain under the existing notification-preference APIs
- the frontend settings screen may save both notification preferences and `user_app_preferences`, but they are stored in separate backend models/routes

## Validation and defaults

Service helpers live in:

- `Backend/app/services/user_preference_service.py`

Current constants:

- `APP_FONT_SIZE_MIN = 80`
- `APP_FONT_SIZE_MAX = 130`
- `APP_FONT_SIZE_STEP = 5`
- `APP_FONT_SIZE_DEFAULT = 100`
- `APP_TRUSTED_DEVICE_DAYS_DEFAULT = 14`
- `APP_TRUSTED_DEVICE_DAYS_MIN = 1`
- `APP_TRUSTED_DEVICE_DAYS_MAX = 90`

## Test checklist

### Automated

Run:

```powershell
python -m pytest -q Backend/app/tests/test_api.py
```

Covered scenarios:

- privileged login returns face-pending MFA response
- remember-me extends stored session lifetime
- app preference route creates and updates `user_app_preferences`

### Manual

1. Apply migrations:
   - `alembic upgrade head`
2. Login as `campus_admin`:
   - confirm the login response has `face_verification_required=true`
   - confirm `session_id` is `null`
3. Complete `POST /api/auth/security/face-verify`:
   - confirm the response returns a full access token and non-null `session_id`
4. Login as a non-privileged user with `remember_me=true`:
   - confirm the resulting session expiry reflects the trusted-device duration
5. Call `GET /api/users/preferences/me`
6. Call `PUT /api/users/preferences/me` with updated `dark_mode_enabled` and `font_size_percent`
7. Sign in on another device and confirm the same preference values are loaded from the backend

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
- bootstrap and demo-seed defaults

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

## Face Runtime Warm-Up

On API startup, the backend may trigger the InsightFace warm-up flow.

- This is controlled by `Backend/app/core/app_settings.py`, not `.env`.
- Warm-up failures are logged but do not block API startup.

Related guide:

- [Face Engine Migration Guide](./BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md)

## Seeder and Bootstrap Flow

Production and demo data are now split into explicit commands:

- `python Backend/bootstrap.py ...`
- `python Backend/seed.py ...`

The backend no longer relies on `SEED_*` env toggles to decide what data to create.

## How to Test

1. Run `pytest Backend/app/tests/test_config.py Backend/app/tests/test_email_service.py Backend/app/tests/test_seeder.py`.
2. Run `pytest Backend/app/tests/test_admin_import_preview_flow.py` to confirm import storage still honors the centralized backend settings object.
3. Start the API and confirm:
   - `EMAIL_TRANSPORT=disabled` allows startup with a warning
   - `EMAIL_TRANSPORT=mailjet_api` fails fast when credentials are incomplete

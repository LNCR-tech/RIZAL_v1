# Backend Runtime Behavior

[<- Back to backend index](./README.md)

This page documents backend behaviors that affect startup or runtime even if you did not touch routes directly.

## Email Startup Validation

On API startup, the backend runs an email transport validation hook. This is intended to fail fast in environments where email is required.

Configuration is driven by environment variables parsed in `Backend/app/core/config.py`.

Related doc:

- [Email Delivery Guide (Gmail + Local Mailpit)](./BACKEND_EMAIL_LOCAL_TESTING_GUIDE.md)

## Face Runtime Warm-Up (InsightFace)

On API startup, the backend may trigger a face-recognition runtime warm-up.

- Controlled by `FACE_WARMUP_ON_STARTUP` (default `true`).
- Warm-up failures are logged but do not block API startup.

For migrations and model-related notes, see:

- [Face Engine Migration Guide](./BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md)


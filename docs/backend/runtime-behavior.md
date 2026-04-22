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

## Governance Membership Derived Roles (SSG/SG/ORG)

Some backend access rules use coarse role checks (ex: `has_any_role(user, ["ssg"])`) while governance scope is stored as governance memberships.

To keep behavior consistent, the backend syncs `user_roles` entries for `ssg`/`sg`/`org` based on a user's active governance memberships whenever governance membership records are assigned/updated/deactivated.

How to test:

1. Assign a student to an `SSG`/`SG`/`ORG` governance unit via the governance membership endpoints.
2. Confirm the user now has the matching DB role (`ssg`/`sg`/`org`) and that sanctions access behaves as expected for that governance scope.

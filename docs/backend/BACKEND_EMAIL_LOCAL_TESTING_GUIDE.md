# Backend Email Delivery Guide (Mailjet / Disabled)

<!--nav-->
[← Backend Changelog](BACKEND_CHANGELOG.md) | [🏠 Home](/README.md) | [Face Attendance Policy →](BACKEND_FACE_ATTENDANCE_MODE_POLICY.md)

---
<!--/nav-->

The backend now supports exactly two outbound email modes:

- `EMAIL_TRANSPORT=disabled`
- `EMAIL_TRANSPORT=mailjet_api`

Gmail API, SMTP, and Mailpit are no longer part of the supported runtime contract.

Important current behavior:

- outbound email delivery is disabled in code for now
- password-reset, onboarding, and notification emails are not sent even when Mailjet settings are present
- notification email-channel attempts are logged as `skipped`, while in-app notifications can still be created

## Required Mailjet Settings

These settings are kept for the future Mailjet path. They do not send mail while code-level outbound delivery is disabled:

```env
EMAIL_TRANSPORT=mailjet_api
EMAIL_SENDER_EMAIL=notifications@example.com
EMAIL_SENDER_NAME=Aura Notifications
EMAIL_REPLY_TO=notifications@example.com
MAILJET_API_KEY=your-mailjet-api-key
MAILJET_API_SECRET=your-mailjet-api-secret
```

Notes:

- `EMAIL_REPLY_TO` is optional.
- Email timeout and startup connection verification defaults now live in `Backend/app/core/app_settings.py`.
- Transactional email templates now use the fixed login URL `https://supervirulently-downless-keven.ngrok-free.dev` unless a specific sender call overrides it explicitly.

## Default Local Behavior

For local development, leave email disabled:

```env
EMAIL_TRANSPORT=disabled
```

That keeps:

- password-reset flows from attempting a real send
- onboarding flows from attempting a real send
- notification flows from attempting a real email send
- API startup stable when Mailjet is not configured

## Verifying Mailjet

Mailjet connectivity is not verified while code-level outbound delivery is disabled. When outbound delivery is re-enabled, Mailjet connectivity is verified automatically at backend startup when `EMAIL_TRANSPORT=mailjet_api` is set.

## Startup Validation Behavior

While code-level outbound delivery is disabled, backend startup:

1. logs that outbound email delivery is disabled in code
2. skips sender validation
3. skips Mailjet credential validation
4. skips Mailjet connectivity checks

When outbound delivery is re-enabled and `EMAIL_TRANSPORT=mailjet_api`, backend startup:

1. validates the configured sender email and sender name
2. validates `MAILJET_API_KEY` and `MAILJET_API_SECRET`
3. logs the active transport summary
4. verifies Mailjet connectivity when backend app settings keep startup verification enabled

If any of those fail after outbound delivery is re-enabled, API startup aborts.

## How to Test

1. Set `EMAIL_TRANSPORT=disabled` and start the backend.
2. Confirm startup succeeds and logs that outbound email is disabled in code.
3. Trigger a password reset, student creation, or notification dispatch.
4. Confirm no email is sent and notification email-channel logs, where applicable, are `skipped`.

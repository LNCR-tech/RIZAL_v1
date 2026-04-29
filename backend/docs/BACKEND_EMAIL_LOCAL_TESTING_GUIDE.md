# Backend Email Delivery Guide (Mailjet / Disabled)

<!--nav-->
[Previous](BACKEND_DB_NORMALIZED_SCHEMA_GUIDE.md) | [Next](BACKEND_FACE_ATTENDANCE_MODE_POLICY.md) | [Home](/README.md)

---
<!--/nav-->

The backend now supports exactly two outbound email modes:

- `EMAIL_TRANSPORT=disabled`
- `EMAIL_TRANSPORT=mailjet_api`

Gmail API, SMTP, and Mailpit are no longer part of the supported runtime contract.

## Required Mailjet Settings

Set these in the root `.env` when you want real outbound mail:

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
- API startup stable when Mailjet is not configured

## Verifying Mailjet

Mailjet connectivity is verified automatically at backend startup when `EMAIL_TRANSPORT=mailjet_api` is set. Check the backend startup logs for confirmation.

## Startup Validation Behavior

When `EMAIL_TRANSPORT=mailjet_api`, backend startup now:

1. validates the configured sender email and sender name
2. validates `MAILJET_API_KEY` and `MAILJET_API_SECRET`
3. logs the active transport summary
4. verifies Mailjet connectivity when backend app settings keep startup verification enabled

If any of those fail, API startup aborts.

## How to Test

1. Set `EMAIL_TRANSPORT=disabled` and start the backend.
2. Confirm startup succeeds and logs that outbound mail is disabled.
3. Set `EMAIL_TRANSPORT=mailjet_api` without credentials and start the backend.
4. Confirm startup fails fast with a Mailjet configuration error.
5. Set valid Mailjet credentials and start the backend.
6. Confirm startup succeeds and logs that Mailjet connectivity is verified.


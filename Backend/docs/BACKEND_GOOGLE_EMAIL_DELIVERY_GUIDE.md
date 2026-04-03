# Backend Google Email Delivery Guide

## Purpose

This guide documents the Gmail API-only mail delivery setup for VALID8 transactional emails such as forgot-password approvals, MFA codes, onboarding emails, and bulk-import account-ready emails.

## Current Backend Contract

- outbound delivery supports only `EMAIL_TRANSPORT=gmail_api`
- the backend refreshes a Google OAuth access token and sends mail through `https://gmail.googleapis.com/gmail/v1/users/me/messages/send`
- the authenticated mailbox comes from `EMAIL_SENDER_EMAIL`
- the visible sender comes from `EMAIL_FROM_EMAIL`
- if `EMAIL_FROM_EMAIL` differs from `EMAIL_SENDER_EMAIL`, the backend requires:
  - a verified Gmail send-as alias
  - `EMAIL_GOOGLE_ALLOW_CUSTOM_FROM=true`
- personal Gmail accounts cannot keep an arbitrary custom `EMAIL_FROM_EMAIL`; the backend falls back to the authenticated Gmail address and logs a warning
- Google Workspace mailboxes can send from a verified alias when the alias exists in Gmail settings and custom-from is enabled

## Runtime Files

- `Backend/app/services/email_service/config.py`
- `Backend/app/services/email_service/transport.py`
- `Backend/app/services/email_service/rendering.py`
- `Backend/app/services/email_service/use_cases.py`
- `Backend/scripts/generate_google_oauth_refresh_token.py`
- `Backend/scripts/send_test_email.py`

## Required Environment Variables

- `EMAIL_TRANSPORT=gmail_api`
- `EMAIL_TIMEOUT_SECONDS`
- `EMAIL_SENDER_EMAIL`
- `EMAIL_FROM_EMAIL`
- `EMAIL_FROM_NAME`
- `EMAIL_REPLY_TO`
- `EMAIL_GOOGLE_ACCOUNT_TYPE`
- `EMAIL_GOOGLE_ALLOW_CUSTOM_FROM`
- `EMAIL_REQUIRED_ON_STARTUP`
- `EMAIL_VERIFY_CONNECTION_ON_STARTUP`
- `GOOGLE_GMAIL_API_BASE_URL`
- `GOOGLE_OAUTH_AUTH_URL`
- `GOOGLE_OAUTH_TOKEN_URL`
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REFRESH_TOKEN`
- `GOOGLE_OAUTH_SCOPES`

## Temporary Migration Alias Support

The backend still reads these legacy env names as fallback aliases during rollout:

- `SMTP_TIMEOUT_SECONDS -> EMAIL_TIMEOUT_SECONDS`
- `SMTP_USERNAME -> EMAIL_SENDER_EMAIL`
- `SMTP_FROM_EMAIL -> EMAIL_FROM_EMAIL`
- `SMTP_FROM_NAME -> EMAIL_FROM_NAME`
- `SMTP_REPLY_TO -> EMAIL_REPLY_TO`
- `SMTP_GOOGLE_ACCOUNT_TYPE -> EMAIL_GOOGLE_ACCOUNT_TYPE`
- `SMTP_GOOGLE_ALLOW_CUSTOM_FROM -> EMAIL_GOOGLE_ALLOW_CUSTOM_FROM`

The SMTP transport itself is removed. Those old names are only compatibility aliases for existing deployments that have not renamed their env vars yet.

## Recommended Deployment Shape

Use one authenticated mailbox for Gmail API delivery:

- personal Gmail:
  - `EMAIL_SENDER_EMAIL=<your@gmail.com>`
  - `EMAIL_FROM_EMAIL=<same Gmail address>`
  - `EMAIL_GOOGLE_ACCOUNT_TYPE=personal`
- Google Workspace mailbox:
  - `EMAIL_SENDER_EMAIL=<mailbox@your-domain>`
  - `EMAIL_FROM_EMAIL=<same mailbox or verified alias>`
  - `EMAIL_GOOGLE_ACCOUNT_TYPE=workspace`
- Google Workspace alias:
  - `EMAIL_SENDER_EMAIL=<real mailbox@your-domain>`
  - `EMAIL_FROM_EMAIL=<verified alias@your-domain>`
  - `EMAIL_GOOGLE_ALLOW_CUSTOM_FROM=true`

## Exact Google Setup Steps

1. Open Google Cloud Console.
2. Create or select the project that will own the Gmail API credentials.
3. Enable the Gmail API.
4. Configure the OAuth consent screen.
5. Add these scopes:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.settings.basic`
6. Create an OAuth client.
7. Run:

`python Backend/scripts/generate_google_oauth_refresh_token.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --login-hint your-mailbox@example.com`

8. Sign in with the Gmail or Google Workspace mailbox that should authenticate API sends.
9. Copy the generated values into deployment config.
10. If `EMAIL_FROM_EMAIL` is a different address, configure it first as a verified Gmail send-as alias.
11. Redeploy the backend.

## Example Gmail API Configuration

```env
EMAIL_TRANSPORT=gmail_api
EMAIL_TIMEOUT_SECONDS=20
EMAIL_SENDER_EMAIL=no-reply@school.edu
EMAIL_FROM_EMAIL=no-reply@school.edu
EMAIL_FROM_NAME=VALID8 Notifications
EMAIL_REPLY_TO=support@school.edu
EMAIL_GOOGLE_ACCOUNT_TYPE=workspace
EMAIL_GOOGLE_ALLOW_CUSTOM_FROM=false
GOOGLE_GMAIL_API_BASE_URL=https://gmail.googleapis.com/gmail/v1
GOOGLE_OAUTH_AUTH_URL=https://accounts.google.com/o/oauth2/v2/auth
GOOGLE_OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
GOOGLE_OAUTH_REFRESH_TOKEN=...
GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/gmail.settings.basic
```

## What The Backend Verifies

- the mail transport is `gmail_api`
- OAuth client ID, client secret, refresh token, and token URL exist
- `EMAIL_SENDER_EMAIL` is a valid address
- `EMAIL_FROM_EMAIL` is valid when supplied
- `EMAIL_FROM_EMAIL` is safe for the detected Google account type
- the Gmail API access token refresh succeeds
- optional startup sender verification succeeds when `EMAIL_VERIFY_CONNECTION_ON_STARTUP=true`

## Local And Production Testing

1. Print the resolved delivery summary:

`python -c "from app.services.email_service import get_email_delivery_summary; print(get_email_delivery_summary())"`

2. Verify connectivity and sender validation without sending:

`python scripts/send_test_email.py --recipient your-address@example.com --check-only`

3. Send a real Gmail API smoke test:

`python scripts/send_test_email.py --recipient your-address@example.com`

4. Test actual app flows:
   - approve a password reset
   - log in with MFA enabled
   - create a user manually
   - run a bulk student import and confirm onboarding emails are queued and logged

## Bulk Import Behavior

Imported student accounts still trigger onboarding email work after successful insert:

- `StudentImportService._flush_batch(...)` queues `app.workers.tasks.send_student_import_onboarding_email`
- the worker task calls `send_import_onboarding_email(...)`
- that use case now sends the same credential-style email body used by create-user flows, including email, temporary password, and login URL
- if task publishing fails, the import still finishes and falls back to an inline Gmail API send attempt for that student
- if the worker path or inline fallback send succeeds, the log row is written with `status=sent`
- if both task publishing and the inline fallback fail, the log row is written with `status=failed`

## Common Failure Cases

### Refresh token invalid

Cause:

- the refresh token was revoked
- the OAuth client was rotated or deleted
- the consent screen is still in testing mode and the token expired

Fix:

- regenerate the refresh token
- move the OAuth consent screen to production
- update `GOOGLE_OAUTH_REFRESH_TOKEN`

### Gmail API scope errors

Cause:

- token created without `gmail.send`
- custom sender verification attempted without `gmail.settings.basic`

Fix:

- reauthorize with:
  - `https://www.googleapis.com/auth/gmail.send`
  - `https://www.googleapis.com/auth/gmail.settings.basic`

### Custom sender rejected

Cause:

- `EMAIL_FROM_EMAIL` is not the authenticated mailbox
- the send-as alias is missing or unverified
- `EMAIL_GOOGLE_ALLOW_CUSTOM_FROM` is still false

Fix:

- use the authenticated mailbox as `EMAIL_FROM_EMAIL`, or
- configure and verify the Gmail send-as alias, then set `EMAIL_GOOGLE_ALLOW_CUSTOM_FROM=true`

### HTTPS connectivity failure

Cause:

- the deployment host cannot reach Google HTTPS endpoints

Fix:

- verify outbound HTTPS access to `oauth2.googleapis.com` and `gmail.googleapis.com`
- rerun `python scripts/send_test_email.py --recipient your-address@example.com --check-only`

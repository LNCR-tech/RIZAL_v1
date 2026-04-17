# Backend Email Delivery Guide (Gmail + Local Mailpit)

This guide explains how backend outbound email now works for cloud deployments and for optional local Mailpit testing.

## Current Runtime Behavior

- `docker-compose.yml` no longer forces `SMTP_HOST=mailpit` for `backend`, `worker`, and `beat`.
- backend services now follow `EMAIL_TRANSPORT` from environment (default fallback: `gmail_api`).
- Mailpit is still available as an optional local SMTP inbox service.

## Cloud (Gmail) Quick Start

Use Gmail API transport in your deployment environment:

- `EMAIL_TRANSPORT=gmail_api`
- `EMAIL_SENDER_EMAIL=<your_gmail_or_workspace_sender>`
- `EMAIL_FROM_EMAIL=<same_or_verified_alias>`
- `GOOGLE_OAUTH_CLIENT_ID=<oauth_client_id>`
- `GOOGLE_OAUTH_CLIENT_SECRET=<oauth_client_secret>`
- `GOOGLE_OAUTH_REFRESH_TOKEN=<oauth_refresh_token>`
- `GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/gmail.settings.basic`

Recommended:

- `EMAIL_REQUIRED_ON_STARTUP=true`
- `EMAIL_VERIFY_CONNECTION_ON_STARTUP=true`

## Optional Local Mailpit Testing

If you want inbox testing without sending real Gmail messages:

1. Set these local env values:
   - `EMAIL_TRANSPORT=smtp`
   - `SMTP_HOST=mailpit`
   - `SMTP_PORT=1025`
   - `SMTP_USERNAME=`
   - `SMTP_PASSWORD=`
   - `SMTP_USE_TLS=false`
   - `SMTP_USE_STARTTLS=false`
2. Start local services:
   - `docker compose up -d --build backend worker beat mailpit`
3. Open Mailpit inbox:
   - `http://localhost:8025`

## Backend Smoke Test Command

From repo root:

`python Backend/scripts/send_test_email.py --recipient test@example.com`

Expected result:

- command exits `0`
- for Gmail transport: recipient receives the message
- for Mailpit transport: message appears in `http://localhost:8025`
- default subject uses `Aura email transport smoke test ...`

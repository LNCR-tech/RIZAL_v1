[<- Back to docs index](../../README.md)

# Backend Email Delivery Guide (Gmail + Local Mailpit)

This guide explains how backend outbound email now works for cloud deployments and for optional local Mailpit testing.

## Current Runtime Behavior

- `docker-compose.yml` no longer forces `SMTP_HOST=mailpit` for `backend`, `worker`, and `beat`.
- backend services now follow `EMAIL_TRANSPORT` from environment (default fallback: `disabled`).
- Mailpit is still available as an optional local SMTP inbox service.
- When `EMAIL_TRANSPORT=disabled`, the backend will not send outbound emails (password reset, import onboarding, etc.).

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

## Enable Mailpit for Local Testing (Docker Compose)

Use this when you want to test email flows locally without sending real Gmail messages.

1. Update root `.env`:

```env
EMAIL_TRANSPORT=smtp
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=false
SMTP_USE_STARTTLS=false
```

2. Start or restart services:

```bash
docker compose up -d --build mailpit backend worker beat
```

3. Open Mailpit web UI:

`http://localhost:8025`

4. Trigger any email flow (password reset, import onboarding email, or smoke test below).

## How to Use Mailpit

- SMTP endpoint inside Docker network: `mailpit:1025`
- Web inbox UI on host machine: `http://localhost:8025`
- Captured emails stay available across container restarts because `docker-compose.yml` now mounts:
  - `mailpit_data:/data`
  - `MP_DATABASE=/data/mailpit.db`

To clear all stored messages, remove the Mailpit volume:

```bash
docker compose down
docker volume rm aura_merged_project_mailpit_data
```

## Switch Back to Gmail Transport

Set `.env` back to Gmail values:

```env
EMAIL_TRANSPORT=gmail_api
EMAIL_SENDER_EMAIL=<your_gmail_or_workspace_sender>
EMAIL_FROM_EMAIL=<same_or_verified_alias>
```

Then restart services:

```bash
docker compose up -d --build backend worker beat
```

## Backend Smoke Test Command

From repo root:

Make sure email delivery is enabled first (set `EMAIL_TRANSPORT` to `smtp` or `gmail_api`).

`python Backend/scripts/send_test_email.py --recipient test@example.com`

Expected result:

- command exits `0`
- for Gmail transport: recipient receives the message
- for Mailpit transport: message appears in `http://localhost:8025`
- if `EMAIL_TRANSPORT=disabled`, the command will fail with an error telling you to enable email delivery
- default subject uses `Aura email transport smoke test ...`


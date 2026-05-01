# Backend Email Delivery Guide (Gmail + Local Mailpit)

> **Status:** ACTIVE
> **Last Updated:** 2026-04-17

## Purpose

This page documents the current backend outbound email behavior for both cloud Gmail delivery and optional local Mailpit testing.

## Current Runtime Behavior

- `docker-compose.yml` no longer forces `SMTP_HOST=mailpit` for `backend`, `worker`, and `beat`
- backend services now follow `EMAIL_TRANSPORT` from environment, with `gmail_api` as the default fallback
- Mailpit remains available as an optional local SMTP inbox service when you explicitly set SMTP transport values

## Cloud Gmail Quick Start

Use Gmail API transport in your deployment or local environment:

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

### Mailpit endpoints

- SMTP listener: `localhost:1025`
- Web inbox UI: `http://localhost:8025`

### Local SMTP transport values

Use these values for Mailpit-backed local delivery:

- `EMAIL_TRANSPORT=smtp`
- `SMTP_HOST=mailpit`
- `SMTP_PORT=1025`
- `SMTP_USERNAME=` blank
- `SMTP_PASSWORD=` blank
- `SMTP_USE_TLS=false`
- `SMTP_USE_STARTTLS=false`
- `EMAIL_TIMEOUT_SECONDS=20`

### Local test steps

1. Start the local stack:

```bash
docker compose up -d --build backend worker beat mailpit
```

2. Open the Mailpit inbox:

```text
http://localhost:8025
```

3. Trigger any backend flow that sends email:

- onboarding import email
- password or security-related notification flow
- a direct smoke test from `Backend/scripts/send_test_email.py`

4. Confirm the message appears in the Mailpit inbox.

## Smoke Test Command

From the repository root, run:

```bash
python Backend/scripts/send_test_email.py --recipient test@example.com
```

Expected result depends on the chosen transport:

- command exits successfully
- for Gmail transport, the recipient receives the message
- for Mailpit transport, the message appears in `http://localhost:8025`
- the default subject uses Aura-branded smoke-test wording

## What To Check When Email Fails

1. confirm the active `EMAIL_TRANSPORT` value and related env vars
2. for Mailpit, confirm `mailpit` is running with `docker compose ps`
3. for Mailpit, confirm backend env values point at `mailpit:1025`
4. inspect `docker compose logs backend --tail 100`
5. inspect `docker compose logs worker --tail 100`
6. verify whether the flow uses async task dispatch instead of inline send

## Documentation Note

This combined doc replaces the need to rely on a tracked root `.env.example` for email setup. The current source of truth is:

- `docker-compose.yml`
- `Backend/app/core/config.py`
- this page

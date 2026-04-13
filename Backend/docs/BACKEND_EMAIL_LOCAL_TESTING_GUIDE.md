# Backend Local Email Testing Guide (Mailpit)

This guide explains how to test backend outbound email locally with Mailpit.

## What Changed

- local Docker Compose includes `mailpit` (SMTP + web inbox)
- backend email transport supports `EMAIL_TRANSPORT=smtp`
- local compose backend services are configured to use:
  - `SMTP_HOST=mailpit`
  - `SMTP_PORT=1025`

## Local Mailpit Endpoints

- Mailpit SMTP: `localhost:1025`
- Mailpit Web UI: `http://localhost:8025`

## Quick Start

1. Start local services:
   - `docker compose up -d --build backend worker beat mailpit`
2. Open Mailpit inbox:
   - `http://localhost:8025`
3. Trigger any backend flow that sends email:
   - onboarding import email
   - password reset approval email
   - `Backend/scripts/send_test_email.py`
4. Verify the message appears in Mailpit.

## Environment Variables

When using SMTP transport locally:

- `EMAIL_TRANSPORT=smtp`
- `EMAIL_TIMEOUT_SECONDS=20`
- `SMTP_HOST=mailpit`
- `SMTP_PORT=1025`
- `SMTP_USERNAME=` (blank for Mailpit default)
- `SMTP_PASSWORD=` (blank for Mailpit default)
- `SMTP_USE_TLS=false`
- `SMTP_USE_STARTTLS=false`

When using Gmail API instead:

- `EMAIL_TRANSPORT=gmail_api`
- keep Google OAuth variables configured (`GOOGLE_OAUTH_CLIENT_ID`, etc.)

## Backend Smoke Test Command

From repo root:

`python Backend/scripts/send_test_email.py --recipient test@example.com`

Expected result:

- command exits `0`
- Mailpit UI shows the new message

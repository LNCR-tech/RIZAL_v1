# Backend Auth Login Performance Guide

## Purpose

This guide explains how login-side effects were moved off the main request path so normal frontend login feels faster without changing the login API contract.

## Main Files

- `Backend/app/routers/auth.py`
- `Backend/app/services/auth_background.py`
- `Backend/app/services/email_service.py`
- `Backend/app/services/notification_center_service.py`
- `Backend/app/worker/tasks.py`
- `Backend/app/database.py`
- `Backend/app/tests/test_auth_background.py`

## What Changed

- normal `/login` no longer waits for account-security email delivery before returning the auth response
- MFA login no longer blocks on the full SMTP send path when async dispatch is available
- Celery is used first for login-side email and notification work
- if Celery publish fails, the backend falls back to FastAPI background tasks so the HTTP response can still finish quickly
- obvious SMTP configuration errors are still validated before scheduling MFA delivery
- forced SQL query logging was removed unless `SQL_ECHO=true`

## Request Flow

### `/login`

1. validate credentials
2. validate account and school state
3. issue token payload
4. record login history
5. queue account-security notification asynchronously
6. commit and return response

### `/login` with MFA

1. validate credentials
2. create MFA challenge
3. validate SMTP configuration
4. queue MFA email asynchronously
5. commit and return MFA challenge response

### `/auth/mfa/verify`

1. verify challenge code
2. issue token payload
3. record login history
4. queue MFA-completed security notification asynchronously
5. commit and return response

## Notes

- route paths did not change
- request and response JSON fields did not change
- login still records DB session and login-history data synchronously
- email and notification side effects are the parts that moved off the request path

## Testing

Run:

`python -m pytest -q`

Recommended manual checks:

1. Log in as a normal student account and confirm the response returns quickly.
2. Log in as an admin or School IT account and confirm MFA challenge creation still works.
3. Complete `/auth/mfa/verify` and confirm the login still succeeds.
4. If Celery is running, confirm login email/notification tasks appear in the worker.
5. If Celery is unavailable, confirm login still returns and background-task fallback keeps the flow working.

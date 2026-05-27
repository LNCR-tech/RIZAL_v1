# Backend Error Logs

A running record of notable errors encountered during development and deployment. Use this as a reference if an error recurs.

---

## ERR-001 — Gmail SMTP 535 Authentication Failed

**Date:** 2026-05-27  
**Context:** Attempting to use Gmail SMTP (`smtp.gmail.com:587`) for transactional email delivery.

**Error:**
```
535-5.7.8 Username and Password not accepted
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted...')
```

**Cause:** Google no longer accepts plain account passwords for SMTP. An App Password must be generated in Google Account → Security → 2-Step Verification → App Passwords. Using the account password directly always fails regardless of credentials.

**Fix Applied:** Switched email transport from `smtp` to `resend` (Resend API). Updated `EMAIL_TRANSPORT=resend` and `RESEND_API_KEY` in `.env.production`. Implemented `_send_via_resend()` in `backend/app/services/email_service/transport.py`.

**If This Recurs:** If reverting to Gmail SMTP, generate an App Password at myaccount.google.com → Security → App Passwords and use that instead of the account password.

---

## ERR-002 — Alembic Revision ID Exceeds VARCHAR(32)

**Date:** 2026-05-27  
**Context:** Creating a new Alembic migration file `0012_school_event_policy_face_flags.py`.

**Error:**
```
sqlalchemy.exc.DataError: (psycopg2.errors.StringDataRightTruncation)
value too long for type character varying(32)
```

**Cause:** The `alembic_version` table stores `version_num` as `VARCHAR(32)`. The revision ID `0012_school_event_policy_face_flags` is 36 characters — exceeds the column limit.

**Fix Applied:** Shortened revision ID to `0012_school_ep_face_flags` (25 characters). Both `revision` in the migration file and the filename must use the shortened form.

**If This Recurs:** Always keep Alembic revision IDs at 32 characters or fewer. Count characters before naming: `len("your_revision_id")`.

---

## ERR-003 — Docker Production Container Reads `.env.production`, Not `.env`

**Date:** 2026-05-27  
**Context:** Updated environment variables in `.env` but backend container still showed old values inside Docker.

**Error:** No hard error — silent misconfiguration. `docker exec ... env | grep EMAIL_TRANSPORT` showed `smtp` after editing `.env` to set `resend`.

**Cause:** `docker-compose.prod.yml` has `env_file: ./.env.production` for all services. Changes to the root `.env` file have no effect on production containers. The `.env` file is used for local development only.

**Fix Applied:** Edited `.env.production` instead, then restarted affected services:
```
docker compose -f docker-compose.prod.yml up -d --force-recreate --no-deps backend worker beat
```

**If This Recurs:** Always check `docker-compose.prod.yml` for the `env_file:` directive. For production, **only edit `.env.production`**. After editing, services must be restarted (`--force-recreate`) to pick up new environment values.

---

## ERR-004 — New Alembic Migration Not Applied After Deploy

**Date:** 2026-05-27  
**Context:** Deployed a new migration (`0013_pwd_reset_tokens`) creating the `password_reset_tokens` table. The `/auth/forgot-password` endpoint started returning 500 because the table did not exist.

**Error:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable)
relation "password_reset_tokens" does not exist
```

**Cause:** The standard deploy command only builds the `migrate` image — it does not run `alembic upgrade head`:
```
docker compose -f docker-compose.prod.yml build migrate && \
docker compose -f docker-compose.prod.yml up -d --force-recreate --no-deps backend worker beat
```
The migration service is a one-shot container (`command: alembic upgrade head`) that only runs if explicitly invoked via `run` or `up`.

**Fix Applied:** Manually ran the migration after deployment:
```
docker compose -f docker-compose.prod.yml run --rm migrate alembic upgrade head
```

**If This Recurs:** Whenever a new migration is added to a deployment, always run migrations explicitly after deploying:
```
docker compose -f docker-compose.prod.yml run --rm migrate alembic upgrade head
```
Check the output — it should show `Running upgrade <prev> -> <new>`. If it says `No new migrations`, the file may not have been deployed or the revision chain may be broken.

---

## ERR-005 — CI Cascade Failure: Seed Data Expunged by Intentional Rollback in `auth_session.py`

**Date:** 2026-05-27 (root cause identified and fixed)  
**Context:** GitHub Actions CI — all backend tests failing. 300+ tests showing `E` (setup error) or `F` (failure) across the entire test suite.

**Error chain (CI logs):**
```
sqlalchemy.orm.exc.ObjectDeletedError: Instance '<User>' has been deleted, or its row is otherwise not present.
ERROR: create_user_session failed for user_id=2; refusing to issue a token without a session row.
assert 401 == 200  (conftest.py:242, campus_admin_token fixture)

[followed by 300+ cascade failures:]
sqlalchemy.exc.PendingRollbackError: ... Original exception was:
  psycopg2.errors.ForeignKeyViolation: insert or update on table "events"
  violates foreign key constraint "events_school_id_fkey"
  DETAIL: Key (school_id)=(1) is not present in table "schools".
```

**Cause:** `auth_session.py:259` contains an intentional `db.rollback()` call before creating the `UserSession` row, designed to flush any errors silently absorbed by optional context helpers (governance, school, face scan) during login:

```python
_user_id = user.id
db.rollback()   # ← intentional clean-slate before UserSession INSERT
create_user_session(db, user=user, ...)
```

In production this is safe — users are committed to the DB, so rollback only expires them (they reload on next access). But in tests, the `_seed()` function in `conftest.py` called `db.flush()` but never `db.commit()`, so ALL seed data (school, users, roles, events) existed only as pending uncommitted inserts. When `db.rollback()` fired during the first login attempt, SQLAlchemy **expunged** every pending object from the session. The user object passed to `create_user_session` became stale → `ObjectDeletedError` → login returns 500/401. With seed data gone, all subsequent test fixture lookups failed, producing the FK violation cascade.

**Fix Applied:** Changed final `db.flush()` to `db.commit()` in `_seed()` (`backend/tests/conftest.py`):
```python
# Before:
db.flush()

# After:
db.commit()
```
Committed seed data survives any `db.rollback()` call — rollback expires objects (triggering a transparent SELECT reload) rather than expunging them entirely.

**Files changed:** `backend/tests/conftest.py` (1 line, commit `bb42a3a5`)

**If This Recurs:** If CI shows a wave of `PendingRollbackError` with "original exception" pointing to a FK violation, check whether `_seed()` commits its data. Also check if any new `db.rollback()` call was added to the login or auth flow that could interact with the shared test session.

---

## ERR-006 — Manual Student Creation Returns 500 When Last Name Is Shorter Than 8 Characters

**Date:** 2026-05-27  
**Context:** `POST /api/users/students/` — creating a student whose last name has fewer than 8 characters.

**Error:**
```
HTTP 500: Failed to create student account: Password must be at least 8 characters
ValueError: Password must be at least 8 characters
```

**Cause:** `User.set_password()` enforces an 8-character minimum:
```python
def set_password(self, password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    ...
```
The manual student creation route uses the student's last name as their default password (`issued_password = last_name.lower()`). Last names shorter than 8 characters (e.g., "Smith" = 5 chars, "Student" = 7 chars) trigger this error, which is caught by the route's generic `except Exception` block and returned as a 500.

The bulk import service (`student_import_service.py`) avoids this by calling `hash_password_bcrypt()` directly, bypassing the length validation.

**Fix Applied:** Replaced `db_user.set_password(issued_password)` with a direct `password_hash=hash_password_bcrypt(issued_password)` in the `UserModel` constructor, matching the bulk import pattern (`backend/app/routers/users/students.py`):

```python
# Before:
db_user = UserModel(email=..., ...)
db_user.set_password(issued_password)

# After:
db_user = UserModel(
    email=...,
    password_hash=hash_password_bcrypt(issued_password),
    ...
)
```

Also added `from app.utils.passwords import hash_password_bcrypt` import to `students.py`.

**Files changed:** `backend/app/routers/users/students.py` (commit `8ab64df1`)

**If This Recurs:** Any place that sets a system-assigned default password (not user-chosen) should use `hash_password_bcrypt()` directly instead of `set_password()`. The 8-char check in `set_password()` is intended only for user-chosen passwords.

---

## ERR-007 — Resend Email Delivery Restricted to Account Owner (Unverified Domain)

**Date:** 2026-05-27  
**Context:** After switching to Resend API, password reset emails sent successfully (200 response from Resend) but only delivered to the Resend account owner email. Emails to other recipients were silently dropped.

**Cause:** Resend only delivers to any recipient once the sending domain is verified. With an unverified domain, Resend restricts delivery to the account owner's email address only (for testing purposes).

**Fix Applied (Partial):** Confirmed the API key and transport work correctly. Domain verification is pending — user to complete DNS record setup in Resend dashboard.

**If This Recurs:** Go to Resend dashboard → Domains → verify that `EMAIL_SENDER_EMAIL`'s domain has DNS records added and shows "Verified" status. Until verified, only the Resend account email receives messages.

---

"""Convert user_sessions.token_jti from CHAR(64) to TEXT.

Revision ID: 0010_user_sessions_jti_text
Revises: 0009_gov_member_perm_ts
Create Date: 2026-05-26 13:30:00.000000

`schema.sql` bootstrapped `user_sessions.token_jti` as `CHAR(64) NOT NULL UNIQUE`.
Postgres CHAR is **blank-padded** — stored values are right-padded with
spaces to 64 characters.

The ORM model (`app/models/platform_features.py`) declares the same
column as `Text` and the JWT layer sends 36-character UUID strings as the
JTI. Postgres's implicit cast between the blank-padded CHAR column and
the TEXT parameter sent by SQLAlchemy can break the `=` comparison in
`assert_session_valid`'s `WHERE token_jti = $1` lookup — the
unpadded 36-char parameter never matches the padded stored value.

Symptom: `create_user_session` INSERT succeeds at login time → JWT
returned to client → next authed request's `assert_session_valid`
returns None for the same JTI → 401 "Session is not valid" → Flutter
logs the user out → "dashboard flashes then login screen" loop.

This migration aligns the DB schema with the ORM model. After it runs,
INSERTs and SELECTs both use TEXT semantics, the comparison is exact,
and the session lookup succeeds.

`rtrim()` in the USING clause strips any trailing spaces that the
CHAR(64) padding left behind on rows already in the table, so existing
sessions also resolve correctly after the migration.
"""

from alembic import op
import sqlalchemy as sa

revision = "0010_user_sessions_jti_text"
down_revision = "0009_gov_member_perm_ts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE user_sessions "
        "ALTER COLUMN token_jti TYPE TEXT USING rtrim(token_jti)"
    ))


def downgrade() -> None:
    # Best-effort: only safe if every existing jti fits in 64 chars
    # (UUID4 strings are 36 chars so this holds in practice).
    op.execute(sa.text(
        "ALTER TABLE user_sessions "
        "ALTER COLUMN token_jti TYPE CHAR(64)"
    ))

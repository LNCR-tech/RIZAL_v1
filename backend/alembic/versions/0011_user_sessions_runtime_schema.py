"""Align legacy user_sessions runtime columns with the ORM.

Revision ID: 0011_user_sessions_runtime_schema
Revises: 0010_user_sessions_jti_text
Create Date: 2026-05-26 14:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0011_user_sessions_runtime_schema"
down_revision = "0010_user_sessions_jti_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Older pilot databases created user_sessions.id as varchar(36) while the
    # ORM inserts UUID values. Convert only this table; users.id is left alone
    # because legacy deployments can have views depending on it.
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
              IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'user_sessions'
                  AND column_name = 'id'
                  AND data_type <> 'uuid'
              ) THEN
                ALTER TABLE user_sessions
                  ALTER COLUMN id TYPE UUID USING id::uuid;
              END IF;
            END $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE user_sessions
              ALTER COLUMN ip_address TYPE TEXT,
              ALTER COLUMN user_agent TYPE TEXT
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE user_sessions
              ALTER COLUMN id TYPE VARCHAR(36) USING id::text,
              ALTER COLUMN ip_address TYPE VARCHAR(64),
              ALTER COLUMN user_agent TYPE VARCHAR(500)
            """
        )
    )

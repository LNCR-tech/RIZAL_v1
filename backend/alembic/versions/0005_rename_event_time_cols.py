"""rename events start_datetime/end_datetime to start_at/end_at

Revision ID: 0005_rename_event_time_cols
Revises: b033a6f7e275
Create Date: 2026-05-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_rename_event_time_cols"
down_revision = "b033a6f7e275"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop any check constraints on events that reference start_datetime.
    # PostgreSQL does not auto-update CHECK expression strings on RENAME COLUMN,
    # so we must drop and recreate the constraint manually.
    op.execute(sa.text("""
        DO $$
        DECLARE r RECORD;
        BEGIN
            FOR r IN
                SELECT conname FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                WHERE t.relname = 'events'
                  AND c.contype = 'c'
                  AND pg_get_constraintdef(c.oid) ILIKE '%start_datetime%'
            LOOP
                EXECUTE format('ALTER TABLE events DROP CONSTRAINT %I', r.conname);
            END LOOP;
        END $$;
    """))

    op.alter_column("events", "start_datetime", new_column_name="start_at")
    op.alter_column("events", "end_datetime", new_column_name="end_at")

    op.create_check_constraint(
        "ck_events_end_after_start", "events", "end_at >= start_at"
    )


def downgrade() -> None:
    op.execute(sa.text("""
        DO $$
        DECLARE r RECORD;
        BEGIN
            FOR r IN
                SELECT conname FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                WHERE t.relname = 'events'
                  AND c.contype = 'c'
                  AND pg_get_constraintdef(c.oid) ILIKE '%start_at%'
            LOOP
                EXECUTE format('ALTER TABLE events DROP CONSTRAINT %I', r.conname);
            END LOOP;
        END $$;
    """))

    op.alter_column("events", "start_at", new_column_name="start_datetime")
    op.alter_column("events", "end_at", new_column_name="end_datetime")

    op.create_check_constraint(
        "ck_events_end_after_start", "events", "end_datetime >= start_datetime"
    )

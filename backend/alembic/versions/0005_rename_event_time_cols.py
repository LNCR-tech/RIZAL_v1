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
    # The deployed DB has both old columns (start_datetime/end_datetime, NOT NULL,
    # no timezone) and new columns (start_at/end_at, nullable, with timezone).
    # All existing rows already have start_at/end_at populated.
    # Drop the old columns and make start_at/end_at NOT NULL.

    # Drop any check constraints referencing the old column names.
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

    op.drop_column("events", "start_datetime")
    op.drop_column("events", "end_datetime")

    op.alter_column("events", "start_at", nullable=False)
    op.alter_column("events", "end_at", nullable=False)

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

    op.alter_column("events", "start_at", nullable=True)
    op.alter_column("events", "end_at", nullable=True)

    op.add_column("events", sa.Column(
        "start_datetime", sa.DateTime(timezone=False), nullable=True
    ))
    op.add_column("events", sa.Column(
        "end_datetime", sa.DateTime(timezone=False), nullable=True
    ))

    op.execute(sa.text(
        "UPDATE events SET start_datetime = start_at AT TIME ZONE 'UTC',"
        " end_datetime = end_at AT TIME ZONE 'UTC'"
    ))

    op.alter_column("events", "start_datetime", nullable=False)
    op.alter_column("events", "end_datetime", nullable=False)

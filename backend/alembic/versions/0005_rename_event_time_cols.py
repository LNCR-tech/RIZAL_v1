"""rename events start_datetime/end_datetime to start_at/end_at

Revision ID: 0005_rename_event_time_cols
Revises: bfdc12357b0c
Create Date: 2026-05-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_rename_event_time_cols"
# Rebased onto bfdc12357b0c (which follows 0004_school_face_feature_flags off
# b033a6f7e275) so the migration history is a single linear chain. The prior
# `b033a6f7e275` parent created two heads after merging origin/main.
down_revision = "bfdc12357b0c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # On the legacy deployed DB this migration drops start_datetime/end_datetime
    # (which existed alongside start_at/end_at) and makes start_at/end_at NOT NULL.
    # On a fresh DB built from schema.sql those old columns never exist and
    # start_at/end_at are already NOT NULL, so every step is guarded.
    op.execute(sa.text("""
        DO $$
        DECLARE r RECORD;
        BEGIN
            -- Drop check constraints referencing the old column names (legacy DB only).
            FOR r IN
                SELECT conname FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                WHERE t.relname = 'events'
                  AND c.contype = 'c'
                  AND pg_get_constraintdef(c.oid) ILIKE '%start_datetime%'
            LOOP
                EXECUTE format('ALTER TABLE events DROP CONSTRAINT %I', r.conname);
            END LOOP;

            -- Drop old columns only if they exist.
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'events' AND column_name = 'start_datetime'
            ) THEN
                ALTER TABLE events DROP COLUMN start_datetime;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'events' AND column_name = 'end_datetime'
            ) THEN
                ALTER TABLE events DROP COLUMN end_datetime;
            END IF;

            -- Make start_at NOT NULL only if it is currently nullable.
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'events' AND column_name = 'start_at'
                  AND is_nullable = 'YES'
            ) THEN
                ALTER TABLE events ALTER COLUMN start_at SET NOT NULL;
            END IF;

            -- Make end_at NOT NULL only if it is currently nullable.
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'events' AND column_name = 'end_at'
                  AND is_nullable = 'YES'
            ) THEN
                ALTER TABLE events ALTER COLUMN end_at SET NOT NULL;
            END IF;

            -- Create check constraint only if it does not already exist.
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                WHERE t.relname = 'events'
                  AND c.contype = 'c'
                  AND c.conname = 'ck_events_end_after_start'
            ) THEN
                ALTER TABLE events
                    ADD CONSTRAINT ck_events_end_after_start CHECK (end_at >= start_at);
            END IF;
        END $$;
    """))


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

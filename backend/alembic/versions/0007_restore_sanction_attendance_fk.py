"""restore sanction_records.attendance_id FK to attendance_records

Revision ID: 0007_restore_sanction_attendance_fk
Revises: 0006_drop_legacy_tables
Create Date: 2026-05-25 00:00:00.000000

Migration 0006 incorrectly dropped sanction_records.attendance_id on deployed
databases where the column already pointed to the legacy attendances table.
The column is still needed — the current model and schema.sql define it as
FK → attendance_records(id).  This migration adds it back where missing.
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_sanction_attend_fk"
down_revision = "0006_drop_legacy_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sanction_records' AND column_name = 'attendance_id'
            ) THEN
                ALTER TABLE sanction_records
                    ADD COLUMN attendance_id BIGINT
                    REFERENCES attendance_records(id) ON DELETE SET NULL;
                CREATE INDEX IF NOT EXISTS ix_sanction_records_attendance_id
                    ON sanction_records(attendance_id);
            END IF;
        END $$;
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sanction_records' AND column_name = 'attendance_id'
            ) THEN
                DROP INDEX IF EXISTS ix_sanction_records_attendance_id;
                ALTER TABLE sanction_records
                    DROP CONSTRAINT IF EXISTS sanction_records_attendance_id_fkey,
                    DROP COLUMN attendance_id;
            END IF;
        END $$;
    """))

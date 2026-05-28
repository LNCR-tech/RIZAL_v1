"""Make legacy schools.name and school_name columns nullable.

The ORM model replaced these columns with legal_name / display_name.
The old columns still exist in the live DB with NOT NULL constraints, which
causes a NotNullViolation on every school INSERT because the new ORM no
longer populates them.  This migration:

  1. Copies any existing non-null values so no data is lost.
  2. Makes both columns nullable so old rows are safe and new inserts work.

Revision ID: 0021
Revises: 0020_drop_event_members_only
Create Date: 2026-05-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020_drop_event_members_only"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # On a fresh database (CI / new install) the legacy `name` and `school_name`
    # columns were never created by the baseline migration, so we must guard every
    # operation with an existence check.  On live databases both columns exist and
    # will be backfilled then made nullable as before.
    op.execute("""
        DO $$
        BEGIN
            -- Backfill name if column exists and has NULL rows
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'schools' AND column_name = 'name'
            ) THEN
                UPDATE schools
                SET name = COALESCE(legal_name, display_name, school_name, 'Unknown')
                WHERE name IS NULL;

                ALTER TABLE schools ALTER COLUMN name DROP NOT NULL;
            END IF;

            -- Backfill school_name if column exists and has NULL rows
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'schools' AND column_name = 'school_name'
            ) THEN
                UPDATE schools
                SET school_name = COALESCE(display_name, legal_name, name, 'Unknown')
                WHERE school_name IS NULL;

                ALTER TABLE schools ALTER COLUMN school_name DROP NOT NULL;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    # Re-populate before restoring NOT NULL
    op.execute("""
        UPDATE schools
        SET name = COALESCE(name, legal_name, display_name, 'Unknown')
    """)
    op.execute("""
        UPDATE schools
        SET school_name = COALESCE(school_name, display_name, legal_name, 'Unknown')
    """)
    op.alter_column("schools", "name", nullable=False)
    op.alter_column("schools", "school_name", nullable=False)

"""Make legacy schools.name and school_name columns nullable.

The ORM model replaced these columns with legal_name / display_name.
The old columns still exist in the live DB with NOT NULL constraints, which
causes a NotNullViolation on every school INSERT because the new ORM no
longer populates them.  This migration:

  1. Copies any existing non-null values so no data is lost.
  2. Makes both columns nullable so old rows are safe and new inserts work.

Revision ID: 0021
Revises: bfdc12357b0c
Create Date: 2026-05-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "bfdc12357b0c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill: copy legal_name → name where name is already null (safety net)
    op.execute("""
        UPDATE schools
        SET name = COALESCE(legal_name, display_name, school_name, 'Unknown')
        WHERE name IS NULL
    """)

    # Backfill: copy display_name → school_name where school_name is null
    op.execute("""
        UPDATE schools
        SET school_name = COALESCE(display_name, legal_name, name, 'Unknown')
        WHERE school_name IS NULL
    """)

    # Now make both legacy columns nullable — new INSERTs will leave them NULL
    # and the application reads display_name / legal_name instead.
    op.alter_column("schools", "name", nullable=True)
    op.alter_column("schools", "school_name", nullable=True)


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

"""Add school_id column to governance_announcements.

The column already exists in production but was missing from migrations,
causing CI test DB builds to fail. Uses IF NOT EXISTS so it is safe to
run against a DB that already has the column.

Revision ID: 0017_gov_ann_school_id
Revises: 0016_stu_num_nullable
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0017_gov_ann_school_id"
down_revision = "0016_stu_num_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE governance_announcements
            ADD COLUMN IF NOT EXISTS school_id BIGINT
            REFERENCES schools(id) ON DELETE CASCADE
    """)
    op.execute("""
        UPDATE governance_announcements ga
        SET school_id = gu.school_id
        FROM governance_units gu
        WHERE ga.governance_unit_id = gu.id
          AND ga.school_id IS NULL
    """)
    op.execute("""
        ALTER TABLE governance_announcements
            ALTER COLUMN school_id SET NOT NULL
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_governance_announcements_school_id
            ON governance_announcements(school_id)
    """)


def downgrade() -> None:
    op.execute("""
        DROP INDEX IF EXISTS ix_governance_announcements_school_id
    """)
    op.execute("""
        ALTER TABLE governance_announcements
            DROP COLUMN IF EXISTS school_id
    """)

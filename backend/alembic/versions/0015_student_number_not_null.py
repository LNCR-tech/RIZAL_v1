"""Restore student_profiles.student_number NOT NULL — student ID is required at creation.

Revision ID: 0015_student_number_not_null
Revises: 0014_student_number_nullable
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_student_number_not_null"
down_revision = "0014_student_number_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Back-fill any NULLs introduced while 0014 was live before restoring NOT NULL.
    op.execute(
        "UPDATE student_profiles SET student_number = 'UNKNOWN-' || id::text WHERE student_number IS NULL"
    )
    op.alter_column(
        "student_profiles",
        "student_number",
        existing_type=sa.Text(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "student_profiles",
        "student_number",
        existing_type=sa.Text(),
        nullable=True,
    )

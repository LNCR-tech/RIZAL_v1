"""Restore student_number to nullable — frontend creates student then assigns ID separately.

Revision ID: 0016_stu_num_nullable
Revises: 0015_student_number_not_null
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_stu_num_nullable"
down_revision = "0015_student_number_not_null"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "student_profiles",
        "student_number",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(
        "UPDATE student_profiles SET student_number = 'UNKNOWN-' || id::text WHERE student_number IS NULL"
    )
    op.alter_column(
        "student_profiles",
        "student_number",
        existing_type=sa.Text(),
        nullable=False,
    )

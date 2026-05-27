"""Make student_profiles.student_number nullable — student ID is optional at creation time.

Revision ID: 0014_student_number_nullable
Revises: 0013_pwd_reset_tokens
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_student_number_nullable"
down_revision = "0013_pwd_reset_tokens"
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
    # Back-fill NULLs before restoring NOT NULL, or this will fail if any exist.
    op.execute(
        "UPDATE student_profiles SET student_number = 'UNKNOWN-' || id::text WHERE student_number IS NULL"
    )
    op.alter_column(
        "student_profiles",
        "student_number",
        existing_type=sa.Text(),
        nullable=False,
    )

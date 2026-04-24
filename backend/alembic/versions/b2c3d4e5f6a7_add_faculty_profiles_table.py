"""add faculty_profiles table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-01 00:01:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "faculty_profiles" not in existing_tables:
        op.create_table(
            "faculty_profiles",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("department_id", sa.Integer(), nullable=True),
            sa.Column("program_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", name="uq_faculty_profiles_user_id"),
        )
        op.create_index("ix_faculty_profiles_id", "faculty_profiles", ["id"], unique=False)
        op.create_index("ix_faculty_profiles_user_id", "faculty_profiles", ["user_id"], unique=False)
        op.create_index("ix_faculty_profiles_department_id", "faculty_profiles", ["department_id"], unique=False)
        op.create_index("ix_faculty_profiles_program_id", "faculty_profiles", ["program_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "faculty_profiles" in existing_tables:
        op.drop_index("ix_faculty_profiles_program_id", table_name="faculty_profiles")
        op.drop_index("ix_faculty_profiles_department_id", table_name="faculty_profiles")
        op.drop_index("ix_faculty_profiles_user_id", table_name="faculty_profiles")
        op.drop_index("ix_faculty_profiles_id", table_name="faculty_profiles")
        op.drop_table("faculty_profiles")

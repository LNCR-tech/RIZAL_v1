"""Use: Implements the database change for add governance announcements and student .
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

add governance announcements and student notes

Revision ID: f2a6b8c9d0e1
Revises: d8e2f4c1b7aa
Create Date: 2026-03-16 18:40:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f2a6b8c9d0e1"
down_revision: Union[str, None] = "d8e2f4c1b7aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


announcement_status_enum = sa.Enum(
    "draft",
    "published",
    "archived",
    name="governance_announcement_status",
    native_enum=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    announcement_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "governance_announcements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("governance_unit_id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", announcement_status_enum, nullable=False, server_default="draft"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["governance_unit_id"], ["governance_units.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_governance_announcements_governance_unit_id",
        "governance_announcements",
        ["governance_unit_id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_announcements_school_id",
        "governance_announcements",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_announcements_status",
        "governance_announcements",
        ["status"],
        unique=False,
    )

    op.create_table(
        "governance_student_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("governance_unit_id", sa.Integer(), nullable=False),
        sa.Column("student_profile_id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["governance_unit_id"], ["governance_units.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "governance_unit_id",
            "student_profile_id",
            name="uq_governance_student_notes_unit_student",
        ),
    )
    op.create_index(
        "ix_governance_student_notes_governance_unit_id",
        "governance_student_notes",
        ["governance_unit_id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_student_notes_school_id",
        "governance_student_notes",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_student_notes_student_profile_id",
        "governance_student_notes",
        ["student_profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_governance_student_notes_student_profile_id", table_name="governance_student_notes")
    op.drop_index("ix_governance_student_notes_school_id", table_name="governance_student_notes")
    op.drop_index("ix_governance_student_notes_governance_unit_id", table_name="governance_student_notes")
    op.drop_table("governance_student_notes")

    op.drop_index("ix_governance_announcements_status", table_name="governance_announcements")
    op.drop_index("ix_governance_announcements_school_id", table_name="governance_announcements")
    op.drop_index("ix_governance_announcements_governance_unit_id", table_name="governance_announcements")
    op.drop_table("governance_announcements")

    bind = op.get_bind()
    announcement_status_enum.drop(bind, checkfirst=True)

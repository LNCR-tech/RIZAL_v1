"""add password reset requests

Revision ID: b7f8c9d0e1f2
Revises: f4a2c1b9d8e7
Create Date: 2026-03-05 21:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7f8c9d0e1f2"
down_revision: Union[str, None] = "f4a2c1b9d8e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("requested_email", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("requested_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_password_reset_requests_id", "password_reset_requests", ["id"], unique=False)
    op.create_index("ix_password_reset_requests_user_id", "password_reset_requests", ["user_id"], unique=False)
    op.create_index("ix_password_reset_requests_school_id", "password_reset_requests", ["school_id"], unique=False)
    op.create_index(
        "ix_password_reset_requests_requested_email",
        "password_reset_requests",
        ["requested_email"],
        unique=False,
    )
    op.create_index("ix_password_reset_requests_status", "password_reset_requests", ["status"], unique=False)
    op.create_index("ix_password_reset_requests_requested_at", "password_reset_requests", ["requested_at"], unique=False)
    op.create_index(
        "ix_password_reset_requests_reviewed_by_user_id",
        "password_reset_requests",
        ["reviewed_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_requests_reviewed_by_user_id", table_name="password_reset_requests")
    op.drop_index("ix_password_reset_requests_requested_at", table_name="password_reset_requests")
    op.drop_index("ix_password_reset_requests_status", table_name="password_reset_requests")
    op.drop_index("ix_password_reset_requests_requested_email", table_name="password_reset_requests")
    op.drop_index("ix_password_reset_requests_school_id", table_name="password_reset_requests")
    op.drop_index("ix_password_reset_requests_user_id", table_name="password_reset_requests")
    op.drop_index("ix_password_reset_requests_id", table_name="password_reset_requests")
    op.drop_table("password_reset_requests")

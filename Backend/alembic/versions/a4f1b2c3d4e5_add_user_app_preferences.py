"""add user app preferences

Revision ID: a4f1b2c3d4e5
Revises: f9c2d4e6a8b1
Create Date: 2026-04-17 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4f1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "f9c2d4e6a8b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_app_preferences",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("dark_mode_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("font_size_percent", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("user_app_preferences")

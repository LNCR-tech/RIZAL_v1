"""add prefix and suffix to users

Revision ID: a1b2c3d4e5f6
Revises: 7d43d19e7a58
Create Date: 2026-05-01 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "7d43d19e7a58"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}

    if "prefix" not in columns:
        op.add_column("users", sa.Column("prefix", sa.String(20), nullable=True))

    if "suffix" not in columns:
        op.add_column("users", sa.Column("suffix", sa.String(20), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}

    if "suffix" in columns:
        op.drop_column("users", "suffix")

    if "prefix" in columns:
        op.drop_column("users", "prefix")

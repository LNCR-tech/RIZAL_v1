"""Use: Implements the database change for add event attendance window controls.
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

add event attendance window controls

Revision ID: e4b7c1d9f6a2
Revises: f2a6b8c9d0e1
Create Date: 2026-03-16 22:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e4b7c1d9f6a2"
down_revision: Union[str, None] = "f2a6b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("early_check_in_minutes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "events",
        sa.Column("sign_out_grace_minutes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "events",
        sa.Column("sign_out_override_until", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "attendances",
        sa.Column("check_in_status", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "attendances",
        sa.Column("check_out_status", sa.String(length=16), nullable=True),
    )

    op.alter_column("events", "early_check_in_minutes", server_default=None)
    op.alter_column("events", "sign_out_grace_minutes", server_default=None)


def downgrade() -> None:
    op.drop_column("attendances", "check_out_status")
    op.drop_column("attendances", "check_in_status")
    op.drop_column("events", "sign_out_override_until")
    op.drop_column("events", "sign_out_grace_minutes")
    op.drop_column("events", "early_check_in_minutes")

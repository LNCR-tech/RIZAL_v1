"""add school and governance event defaults

Revision ID: f5d2c8a1b4e9
Revises: e4b7c1d9f6a2
Create Date: 2026-03-16 23:45:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f5d2c8a1b4e9"
down_revision: Union[str, None] = "e4b7c1d9f6a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "school_settings",
        sa.Column(
            "event_default_early_check_in_minutes",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
    )
    op.add_column(
        "school_settings",
        sa.Column(
            "event_default_late_threshold_minutes",
            sa.Integer(),
            nullable=False,
            server_default="10",
        ),
    )
    op.add_column(
        "school_settings",
        sa.Column(
            "event_default_sign_out_grace_minutes",
            sa.Integer(),
            nullable=False,
            server_default="20",
        ),
    )
    op.add_column(
        "governance_units",
        sa.Column("event_default_early_check_in_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "governance_units",
        sa.Column("event_default_late_threshold_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "governance_units",
        sa.Column("event_default_sign_out_grace_minutes", sa.Integer(), nullable=True),
    )

    op.alter_column("school_settings", "event_default_early_check_in_minutes", server_default=None)
    op.alter_column("school_settings", "event_default_late_threshold_minutes", server_default=None)
    op.alter_column("school_settings", "event_default_sign_out_grace_minutes", server_default=None)


def downgrade() -> None:
    op.drop_column("governance_units", "event_default_sign_out_grace_minutes")
    op.drop_column("governance_units", "event_default_late_threshold_minutes")
    op.drop_column("governance_units", "event_default_early_check_in_minutes")
    op.drop_column("school_settings", "event_default_sign_out_grace_minutes")
    op.drop_column("school_settings", "event_default_late_threshold_minutes")
    op.drop_column("school_settings", "event_default_early_check_in_minutes")

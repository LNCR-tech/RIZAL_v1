"""Use: Implements the database change for add event attendance override windows.
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

add event attendance override windows

Revision ID: b1a2c3d4e5f6
Revises: f5d2c8a1b4e9
Create Date: 2026-03-21 21:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, None] = "f5d2c8a1b4e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("events", sa.Column("present_until_override_at", sa.DateTime(), nullable=True))
    op.add_column("events", sa.Column("late_until_override_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "late_until_override_at")
    op.drop_column("events", "present_until_override_at")

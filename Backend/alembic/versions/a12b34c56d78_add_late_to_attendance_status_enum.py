"""add late to attendance status enum

Revision ID: a12b34c56d78
Revises: f8b2c1d4e6a7
Create Date: 2026-03-11 13:20:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a12b34c56d78"
down_revision: Union[str, None] = "f8b2c1d4e6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE attendancestatus ADD VALUE IF NOT EXISTS 'late'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely in place.
    pass


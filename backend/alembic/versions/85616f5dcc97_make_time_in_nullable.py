"""make time_in nullable

Revision ID: 85616f5dcc97
Revises: h9i0j1k2l3m4
Create Date: 2026-04-29 00:09:08.234873

Drops the NOT NULL constraint and the auto-populated default on
attendances.time_in so that students who never signed in keep a real NULL
value instead of an auto-filled `now()` timestamp.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85616f5dcc97'
down_revision: Union[str, None] = 'h9i0j1k2l3m4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow attendances.time_in to be NULL and drop any server-side default."""
    op.alter_column(
        "attendances",
        "time_in",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
        server_default=None,
    )


def downgrade() -> None:
    """Restore the previous NOT NULL constraint on attendances.time_in.

    Auto-fills any currently-NULL rows with the row's time_out (if present) or
    the current UTC timestamp so the constraint can be re-applied without
    losing rows.
    """
    op.execute(
        """
        UPDATE attendances
        SET time_in = COALESCE(time_in, time_out, NOW())
        WHERE time_in IS NULL
        """
    )
    op.alter_column(
        "attendances",
        "time_in",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

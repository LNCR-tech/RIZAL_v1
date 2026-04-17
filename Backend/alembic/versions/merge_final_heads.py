"""merge diverged heads

Revision ID: merge_final_heads
Revises: a4f1b2c3d4e5, e2f7a1c9d4b6
Create Date: 2026-04-17 17:21:00.000000
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "merge_final_heads"
down_revision: Union[str, Sequence[str], None] = ("a4f1b2c3d4e5", "e2f7a1c9d4b6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge the two diverged heads."""
    pass


def downgrade() -> None:
    """No-op on downgrade."""
    pass

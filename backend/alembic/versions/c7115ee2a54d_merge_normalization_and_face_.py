"""merge normalization and face recognition heads

Revision ID: c7115ee2a54d
Revises: a9f3c1e2d4b5, f7a8b9c0d1e2
Create Date: 2026-04-27 05:17:23.653558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7115ee2a54d'
down_revision: Union[str, None] = ('a9f3c1e2d4b5', 'f7a8b9c0d1e2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

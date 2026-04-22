"""initial_baseline

Revision ID: e79235331d71
Revises: 
Create Date: 2026-04-18 16:46:41.989921

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e79235331d71'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Neutralized baseline - protecting all existing tables."""
    pass


def downgrade() -> None:
    """No-op."""
    pass

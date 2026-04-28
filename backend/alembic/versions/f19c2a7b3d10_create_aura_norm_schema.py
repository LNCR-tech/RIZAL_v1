"""create aura_norm normalized schema (side-by-side)

Revision ID: f19c2a7b3d10
Revises: e6f7a8b9c0d1
Create Date: 2026-04-26
"""

from alembic import op

revision = "f19c2a7b3d10"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # aura_norm was a deprecated experimental schema — no-op.
    pass


def downgrade() -> None:
    pass

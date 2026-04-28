"""Replace public schema with normalized schema

Revision ID: a9f3c1e2d4b5
Revises: f19c2a7b3d10
Create Date: 2026-04-27
"""

from alembic import op

revision = "a9f3c1e2d4b5"
down_revision = "f19c2a7b3d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # aura_norm was a deprecated experimental schema — no-op.
    pass


def downgrade() -> None:
    pass

"""Drop members_only column from events — governance_unit_id presence is the restriction signal.

Revision ID: 0020_drop_event_members_only
Revises: 0019_event_members_only
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0020_drop_event_members_only"
down_revision = "0019_event_members_only"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("events", "members_only")


def downgrade() -> None:
    op.add_column(
        "events",
        sa.Column("members_only", sa.Boolean(), nullable=False, server_default="false"),
    )

"""Make attendance timestamps timezone-aware UTC.

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-04-25 13:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c4d5e6f7a8b9"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "attendances" not in inspector.get_table_names():
        return
    op.execute(
        """
        ALTER TABLE attendances
        ALTER COLUMN time_in TYPE TIMESTAMP WITH TIME ZONE
        USING time_in AT TIME ZONE 'UTC',
        ALTER COLUMN time_out TYPE TIMESTAMP WITH TIME ZONE
        USING time_out AT TIME ZONE 'UTC'
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "attendances" not in inspector.get_table_names():
        return
    op.execute(
        """
        ALTER TABLE attendances
        ALTER COLUMN time_in TYPE TIMESTAMP WITHOUT TIME ZONE
        USING time_in AT TIME ZONE 'UTC',
        ALTER COLUMN time_out TYPE TIMESTAMP WITHOUT TIME ZONE
        USING time_out AT TIME ZONE 'UTC'
        """
    )

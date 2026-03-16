"""add should_prompt_password_change to users

Revision ID: 1e5b4a7c9d01
Revises: 9b3e1f2c4d5a
Create Date: 2026-03-15 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1e5b4a7c9d01"
down_revision: Union[str, None] = "9b3e1f2c4d5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "should_prompt_password_change",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("users", "should_prompt_password_change", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "should_prompt_password_change")

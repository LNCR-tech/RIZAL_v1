"""allow_platform_admin_without_school_scope

Revision ID: f4a2c1b9d8e7
Revises: e1c3b7f4a6d9
Create Date: 2026-03-04 12:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f4a2c1b9d8e7"
down_revision: Union[str, None] = "e1c3b7f4a6d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "school_id", existing_type=sa.Integer(), nullable=True)

    # Platform admins are global and should not be tenant-bound.
    op.execute(
        """
        UPDATE users u
        SET school_id = NULL
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = u.id
          AND r.name = 'admin'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET school_id = (SELECT id FROM schools ORDER BY id ASC LIMIT 1)
        WHERE school_id IS NULL
        """
    )
    op.alter_column("users", "school_id", existing_type=sa.Integer(), nullable=False)

"""Use: Implements the database change for seed missing sg and org roles.
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

seed missing sg and org roles

Revision ID: 9c4d2e7f1a8b
Revises: 8b7e6d5c4a3f
Create Date: 2026-03-15 23:30:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9c4d2e7f1a8b"
down_revision: Union[str, None] = "8b7e6d5c4a3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO roles (name)
        SELECT 'sg'
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'sg')
        """
    )
    op.execute(
        """
        INSERT INTO roles (name)
        SELECT 'org'
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'org')
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM user_roles
        WHERE role_id IN (
            SELECT id FROM roles WHERE name IN ('sg', 'org')
        )
        """
    )
    op.execute("DELETE FROM roles WHERE name IN ('sg', 'org')")

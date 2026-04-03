"""Use: Implements the database change for add governance unit description and ssg .
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

add governance unit description and ssg setup defaults

Revision ID: 8b7e6d5c4a3f
Revises: 7c9e4b2a1d33
Create Date: 2026-03-15 18:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b7e6d5c4a3f"
down_revision: Union[str, None] = "7c9e4b2a1d33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_SSG_DESCRIPTION = "Fixed campus-wide student government unit for the school."


def upgrade() -> None:
    op.add_column("governance_units", sa.Column("description", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE governance_units
            SET description = :default_description
            WHERE unit_type = 'SSG'
              AND (description IS NULL OR TRIM(description) = '')
            """
        ).bindparams(default_description=DEFAULT_SSG_DESCRIPTION)
    )


def downgrade() -> None:
    op.drop_column("governance_units", "description")

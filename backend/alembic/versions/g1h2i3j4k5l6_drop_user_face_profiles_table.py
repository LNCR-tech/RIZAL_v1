"""drop_user_face_profiles_table

Revision ID: g1h2i3j4k5l6
Revises: f7a8b9c0d1e2
Create Date: 2026-04-27

"""
from alembic import op

revision = 'g1h2i3j4k5l6'
down_revision = 'c7115ee2a54d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('user_face_profiles')


def downgrade() -> None:
    # Intentionally not recreating the table — restore from db_schema_legacy.sql if needed.
    pass

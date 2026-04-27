"""add using_default_import_password to users

Revision ID: g8h9i0j1k2l3
Revises: f7a8b9c0d1e2
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g8h9i0j1k2l3'
down_revision = 'f7a8b9c0d1e2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('using_default_import_password', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('users', 'using_default_import_password')

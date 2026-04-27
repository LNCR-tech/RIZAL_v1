"""add using_default_import_password to users

Revision ID: g8h9i0j1k2l3
Revises: f7a8b9c0d1e2
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'g8h9i0j1k2l3'
down_revision = 'f7a8b9c0d1e2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('using_default_import_password', sa.Boolean(), nullable=False, server_default='false'))

    conn = op.get_bind()
    conn.execute(text("""
        UPDATE users
        SET using_default_import_password = true
        WHERE id IN (
            SELECT DISTINCT u.id
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.code = 'student'
        )
    """))


def downgrade():
    op.drop_column('users', 'using_default_import_password')

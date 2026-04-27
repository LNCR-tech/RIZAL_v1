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
    # Add the column with default False
    op.add_column('users', sa.Column('using_default_import_password', sa.Boolean(), nullable=False, server_default='false'))
    
    # Set to True for existing students who haven't changed their password yet
    # (students with must_change_password=True and have student role)
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE users
        SET using_default_import_password = true
        WHERE must_change_password = true
        AND id IN (
            SELECT DISTINCT u.id
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'student'
        )
    """))

    # Set to True for ALL existing students (they all have default import passwords)
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE users
        SET using_default_import_password = true
        WHERE id IN (
            SELECT DISTINCT u.id
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'student'
        )
    """))


def downgrade():
    op.drop_column('users', 'using_default_import_password')

"""fix existing students default password flag

Revision ID: h9i0j1k2l3m4
Revises: g8h9i0j1k2l3
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'h9i0j1k2l3m4'
down_revision = 'g8h9i0j1k2l3'
branch_labels = None
depends_on = None


def upgrade():
    # Set using_default_import_password = true for ALL existing students
    # They all have lowercase last name as default password
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
    # Revert all students back to false
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE users
        SET using_default_import_password = false
        WHERE id IN (
            SELECT DISTINCT u.id
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'student'
        )
    """))

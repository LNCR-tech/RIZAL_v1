"""Use: Implements the database change for cleanup legacy role records.
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

cleanup legacy role records

Revision ID: b4c8f12d9e77
Revises: 9c4d2e7f1a8b
Create Date: 2026-03-15 23:55:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b4c8f12d9e77"
down_revision: Union[str, None] = "9c4d2e7f1a8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _scalar(connection, statement: str, **params):
    return connection.execute(sa.text(statement), params).scalar()


def upgrade() -> None:
    connection = op.get_bind()

    campus_admin_id = _scalar(connection, "SELECT id FROM roles WHERE name = :name", name="campus_admin")
    school_it_id = _scalar(connection, "SELECT id FROM roles WHERE name = :name", name="school_IT")

    if campus_admin_id is None and school_it_id is not None:
        connection.execute(
            sa.text("UPDATE roles SET name = :new_name WHERE id = :role_id"),
            {"new_name": "campus_admin", "role_id": school_it_id},
        )
        campus_admin_id = school_it_id
        school_it_id = None
    elif campus_admin_id is None and school_it_id is None:
        connection.execute(sa.text("INSERT INTO roles (name) VALUES (:name)"), {"name": "campus_admin"})
        campus_admin_id = _scalar(connection, "SELECT id FROM roles WHERE name = :name", name="campus_admin")
    elif campus_admin_id is not None and school_it_id is not None and campus_admin_id != school_it_id:
        connection.execute(
            sa.text(
                """
                UPDATE user_roles
                SET role_id = :campus_admin_id
                WHERE role_id = :school_it_id
                """
            ),
            {"campus_admin_id": campus_admin_id, "school_it_id": school_it_id},
        )
        connection.execute(
            sa.text("DELETE FROM roles WHERE id = :role_id"),
            {"role_id": school_it_id},
        )

    for role_name in ("sg", "org"):
        role_id = _scalar(connection, "SELECT id FROM roles WHERE name = :name", name=role_name)
        if role_id is None:
            continue

        connection.execute(
            sa.text("UPDATE governance_members SET role_id = NULL WHERE role_id = :role_id"),
            {"role_id": role_id},
        )
        connection.execute(
            sa.text("DELETE FROM user_roles WHERE role_id = :role_id"),
            {"role_id": role_id},
        )
        connection.execute(
            sa.text("DELETE FROM roles WHERE id = :role_id"),
            {"role_id": role_id},
        )


def downgrade() -> None:
    connection = op.get_bind()

    school_it_id = _scalar(connection, "SELECT id FROM roles WHERE name = :name", name="school_IT")
    campus_admin_id = _scalar(connection, "SELECT id FROM roles WHERE name = :name", name="campus_admin")

    if school_it_id is None and campus_admin_id is not None:
        connection.execute(
            sa.text("UPDATE roles SET name = :new_name WHERE id = :role_id"),
            {"new_name": "school_IT", "role_id": campus_admin_id},
        )
    elif school_it_id is None:
        connection.execute(sa.text("INSERT INTO roles (name) VALUES (:name)"), {"name": "school_IT"})

    for role_name in ("sg", "org"):
        role_id = _scalar(connection, "SELECT id FROM roles WHERE name = :name", name=role_name)
        if role_id is None:
            connection.execute(sa.text("INSERT INTO roles (name) VALUES (:name)"), {"name": role_name})

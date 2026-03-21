"""Use: Implements the database change for drop legacy governance role artifacts.
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

drop legacy governance role artifacts

Revision ID: c3d91e4ab2f6
Revises: b4c8f12d9e77
Create Date: 2026-03-16 01:40:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3d91e4ab2f6"
down_revision: Union[str, None] = "b4c8f12d9e77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _index_exists(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _scalar(connection, statement: str, **params):
    return connection.execute(sa.text(statement), params).scalar()


def _ensure_student_role(connection) -> int:
    student_role_id = _scalar(connection, "SELECT id FROM roles WHERE name = :name", name="student")
    if student_role_id is not None:
        return student_role_id

    connection.execute(sa.text("INSERT INTO roles (name) VALUES (:name)"), {"name": "student"})
    return _scalar(connection, "SELECT id FROM roles WHERE name = :name", name="student")


def _drop_governance_member_role_column(connection, inspector: sa.Inspector) -> None:
    if not _column_exists(inspector, "governance_members", "role_id"):
        return

    for foreign_key in inspector.get_foreign_keys("governance_members"):
        constrained_columns = foreign_key.get("constrained_columns") or []
        constraint_name = foreign_key.get("name")
        if constrained_columns == ["role_id"] and constraint_name:
            op.drop_constraint(constraint_name, "governance_members", type_="foreignkey")

    if _index_exists(inspector, "governance_members", "ix_governance_members_role_id"):
        op.drop_index("ix_governance_members_role_id", table_name="governance_members")

    with op.batch_alter_table("governance_members") as batch_op:
        batch_op.drop_column("role_id")


def _drop_legacy_tables(inspector: sa.Inspector) -> None:
    if _table_exists(inspector, "event_ssg_association"):
        op.drop_table("event_ssg_association")

    if _table_exists(inspector, "ssg_profiles"):
        if _index_exists(inspector, "ssg_profiles", "ix_ssg_profiles_user_id"):
            op.drop_index("ix_ssg_profiles_user_id", table_name="ssg_profiles")
        if _index_exists(inspector, "ssg_profiles", "ix_ssg_profiles_position"):
            op.drop_index("ix_ssg_profiles_position", table_name="ssg_profiles")
        op.drop_table("ssg_profiles")


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    student_role_id = _ensure_student_role(connection)

    for role_name in ("ssg", "event-organizer"):
        role_id = _scalar(connection, "SELECT id FROM roles WHERE name = :name", name=role_name)
        if role_id is None:
            continue

        connection.execute(
            sa.text(
                """
                INSERT INTO user_roles (user_id, role_id)
                SELECT DISTINCT user_roles.user_id, :student_role_id
                FROM user_roles
                JOIN users ON users.id = user_roles.user_id
                WHERE user_roles.role_id = :legacy_role_id
                  AND users.school_id IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1
                    FROM user_roles existing
                    WHERE existing.user_id = user_roles.user_id
                      AND existing.role_id = :student_role_id
                  )
                """
            ),
            {
                "student_role_id": student_role_id,
                "legacy_role_id": role_id,
            },
        )

        connection.execute(
            sa.text("DELETE FROM user_roles WHERE role_id = :role_id"),
            {"role_id": role_id},
        )
        connection.execute(
            sa.text("DELETE FROM roles WHERE id = :role_id"),
            {"role_id": role_id},
        )

    _drop_governance_member_role_column(connection, inspector)
    inspector = sa.inspect(connection)
    _drop_legacy_tables(inspector)


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    for role_name in ("ssg", "event-organizer"):
        role_id = _scalar(connection, "SELECT id FROM roles WHERE name = :name", name=role_name)
        if role_id is None:
            connection.execute(sa.text("INSERT INTO roles (name) VALUES (:name)"), {"name": role_name})

    if not _column_exists(inspector, "governance_members", "role_id"):
        with op.batch_alter_table("governance_members") as batch_op:
            batch_op.add_column(sa.Column("role_id", sa.Integer(), nullable=True))
        op.create_index("ix_governance_members_role_id", "governance_members", ["role_id"], unique=False)
        op.create_foreign_key(
            "fk_governance_members_role_id_roles",
            "governance_members",
            "roles",
            ["role_id"],
            ["id"],
            ondelete="SET NULL",
        )

    inspector = sa.inspect(connection)
    if not _table_exists(inspector, "ssg_profiles"):
        op.create_table(
            "ssg_profiles",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("position", sa.String(length=100), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_ssg_profiles_position", "ssg_profiles", ["position"], unique=False)
        op.create_index("ix_ssg_profiles_user_id", "ssg_profiles", ["user_id"], unique=True)

    inspector = sa.inspect(connection)
    if not _table_exists(inspector, "event_ssg_association"):
        op.create_table(
            "event_ssg_association",
            sa.Column("event_id", sa.Integer(), nullable=False),
            sa.Column("ssg_profile_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
            sa.ForeignKeyConstraint(["ssg_profile_id"], ["ssg_profiles.id"]),
            sa.PrimaryKeyConstraint("event_id", "ssg_profile_id"),
        )

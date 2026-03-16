"""add governance hierarchy management

Revision ID: 6f8c1234ab56
Revises: 1e5b4a7c9d01
Create Date: 2026-03-15 12:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f8c1234ab56"
down_revision: Union[str, None] = "1e5b4a7c9d01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


governance_unit_type_enum = sa.Enum(
    "SSG",
    "SG",
    "ORG",
    name="governance_unit_type",
    native_enum=False,
)
governance_permission_code_enum = sa.Enum(
    "create_sg",
    "create_org",
    "manage_students",
    "view_students",
    "manage_members",
    "manage_events",
    "manage_attendance",
    "manage_announcements",
    "assign_permissions",
    name="governance_permission_code",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "governance_units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("unit_code", sa.String(length=50), nullable=False),
        sa.Column("unit_name", sa.String(length=255), nullable=False),
        sa.Column("unit_type", governance_unit_type_enum, nullable=False),
        sa.Column("parent_unit_id", sa.Integer(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("program_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_unit_id"], ["governance_units.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "unit_code", name="uq_governance_units_school_unit_code"),
    )
    op.create_index("ix_governance_units_id", "governance_units", ["id"], unique=False)
    op.create_index("ix_governance_units_unit_code", "governance_units", ["unit_code"], unique=False)
    op.create_index("ix_governance_units_unit_type", "governance_units", ["unit_type"], unique=False)
    op.create_index("ix_governance_units_parent_unit_id", "governance_units", ["parent_unit_id"], unique=False)
    op.create_index("ix_governance_units_school_id", "governance_units", ["school_id"], unique=False)
    op.create_index("ix_governance_units_department_id", "governance_units", ["department_id"], unique=False)
    op.create_index("ix_governance_units_program_id", "governance_units", ["program_id"], unique=False)
    op.create_index("ix_governance_units_created_by_user_id", "governance_units", ["created_by_user_id"], unique=False)
    op.create_index("ix_governance_units_is_active", "governance_units", ["is_active"], unique=False)

    op.create_table(
        "governance_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("permission_code", governance_permission_code_enum, nullable=False),
        sa.Column("permission_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_governance_permissions_id", "governance_permissions", ["id"], unique=False)
    op.create_index(
        "ix_governance_permissions_permission_code",
        "governance_permissions",
        ["permission_code"],
        unique=True,
    )

    op.create_table(
        "governance_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("governance_unit_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("position_title", sa.String(length=100), nullable=True),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["governance_unit_id"], ["governance_units.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("governance_unit_id", "user_id", name="uq_governance_members_unit_user"),
    )
    op.create_index("ix_governance_members_id", "governance_members", ["id"], unique=False)
    op.create_index(
        "ix_governance_members_governance_unit_id",
        "governance_members",
        ["governance_unit_id"],
        unique=False,
    )
    op.create_index("ix_governance_members_user_id", "governance_members", ["user_id"], unique=False)
    op.create_index("ix_governance_members_role_id", "governance_members", ["role_id"], unique=False)
    op.create_index(
        "ix_governance_members_assigned_by_user_id",
        "governance_members",
        ["assigned_by_user_id"],
        unique=False,
    )
    op.create_index("ix_governance_members_is_active", "governance_members", ["is_active"], unique=False)

    op.create_table(
        "governance_unit_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("governance_unit_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column("granted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["governance_unit_id"], ["governance_units.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["permission_id"], ["governance_permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "governance_unit_id",
            "permission_id",
            name="uq_governance_unit_permissions_unit_permission",
        ),
    )
    op.create_index(
        "ix_governance_unit_permissions_id",
        "governance_unit_permissions",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_unit_permissions_governance_unit_id",
        "governance_unit_permissions",
        ["governance_unit_id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_unit_permissions_permission_id",
        "governance_unit_permissions",
        ["permission_id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_unit_permissions_granted_by_user_id",
        "governance_unit_permissions",
        ["granted_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_unit_permissions_created_at",
        "governance_unit_permissions",
        ["created_at"],
        unique=False,
    )

    governance_permissions_table = sa.table(
        "governance_permissions",
        sa.column("permission_code", governance_permission_code_enum),
        sa.column("permission_name", sa.String(length=100)),
        sa.column("description", sa.Text()),
    )
    op.bulk_insert(
        governance_permissions_table,
        [
            {
                "permission_code": "create_sg",
                "permission_name": "Create SG",
                "description": "Allows members of the unit to create SG child units.",
            },
            {
                "permission_code": "create_org",
                "permission_name": "Create ORG",
                "description": "Allows members of the unit to create ORG child units.",
            },
            {
                "permission_code": "manage_students",
                "permission_name": "Manage Students",
                "description": "Allows members of the unit to manage students within their allowed scope.",
            },
            {
                "permission_code": "view_students",
                "permission_name": "View Students",
                "description": "Allows members of the unit to view students within their allowed scope.",
            },
            {
                "permission_code": "manage_members",
                "permission_name": "Manage Members",
                "description": "Allows members of the unit to manage governance memberships.",
            },
            {
                "permission_code": "manage_events",
                "permission_name": "Manage Events",
                "description": "Allows members of the unit to manage events within their allowed scope.",
            },
            {
                "permission_code": "manage_attendance",
                "permission_name": "Manage Attendance",
                "description": "Allows members of the unit to manage attendance within their allowed scope.",
            },
            {
                "permission_code": "manage_announcements",
                "permission_name": "Manage Announcements",
                "description": "Allows members of the unit to publish and manage announcements.",
            },
            {
                "permission_code": "assign_permissions",
                "permission_name": "Assign Permissions",
                "description": "Allows members of the unit to assign governance permissions.",
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_governance_unit_permissions_created_at", table_name="governance_unit_permissions")
    op.drop_index("ix_governance_unit_permissions_granted_by_user_id", table_name="governance_unit_permissions")
    op.drop_index("ix_governance_unit_permissions_permission_id", table_name="governance_unit_permissions")
    op.drop_index("ix_governance_unit_permissions_governance_unit_id", table_name="governance_unit_permissions")
    op.drop_index("ix_governance_unit_permissions_id", table_name="governance_unit_permissions")
    op.drop_table("governance_unit_permissions")

    op.drop_index("ix_governance_members_is_active", table_name="governance_members")
    op.drop_index("ix_governance_members_assigned_by_user_id", table_name="governance_members")
    op.drop_index("ix_governance_members_role_id", table_name="governance_members")
    op.drop_index("ix_governance_members_user_id", table_name="governance_members")
    op.drop_index("ix_governance_members_governance_unit_id", table_name="governance_members")
    op.drop_index("ix_governance_members_id", table_name="governance_members")
    op.drop_table("governance_members")

    op.drop_index("ix_governance_permissions_permission_code", table_name="governance_permissions")
    op.drop_index("ix_governance_permissions_id", table_name="governance_permissions")
    op.drop_table("governance_permissions")

    op.drop_index("ix_governance_units_is_active", table_name="governance_units")
    op.drop_index("ix_governance_units_created_by_user_id", table_name="governance_units")
    op.drop_index("ix_governance_units_program_id", table_name="governance_units")
    op.drop_index("ix_governance_units_department_id", table_name="governance_units")
    op.drop_index("ix_governance_units_school_id", table_name="governance_units")
    op.drop_index("ix_governance_units_parent_unit_id", table_name="governance_units")
    op.drop_index("ix_governance_units_unit_type", table_name="governance_units")
    op.drop_index("ix_governance_units_unit_code", table_name="governance_units")
    op.drop_index("ix_governance_units_id", table_name="governance_units")
    op.drop_table("governance_units")

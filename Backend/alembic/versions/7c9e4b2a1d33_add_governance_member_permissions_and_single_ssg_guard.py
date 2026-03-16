"""add governance member permissions and single ssg guard

Revision ID: 7c9e4b2a1d33
Revises: 6f8c1234ab56
Create Date: 2026-03-15 20:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c9e4b2a1d33"
down_revision: Union[str, None] = "6f8c1234ab56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "governance_member_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("governance_member_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column("granted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(
            ["governance_member_id"],
            ["governance_members.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["granted_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["permission_id"], ["governance_permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "governance_member_id",
            "permission_id",
            name="uq_governance_member_permissions_member_permission",
        ),
    )
    op.create_index(
        "ix_governance_member_permissions_id",
        "governance_member_permissions",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_member_permissions_governance_member_id",
        "governance_member_permissions",
        ["governance_member_id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_member_permissions_permission_id",
        "governance_member_permissions",
        ["permission_id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_member_permissions_granted_by_user_id",
        "governance_member_permissions",
        ["granted_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_governance_member_permissions_created_at",
        "governance_member_permissions",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        "uq_governance_units_single_ssg_per_school",
        "governance_units",
        ["school_id"],
        unique=True,
        postgresql_where=sa.text("unit_type = 'SSG'"),
    )


def downgrade() -> None:
    op.drop_index("uq_governance_units_single_ssg_per_school", table_name="governance_units")

    op.drop_index(
        "ix_governance_member_permissions_created_at",
        table_name="governance_member_permissions",
    )
    op.drop_index(
        "ix_governance_member_permissions_granted_by_user_id",
        table_name="governance_member_permissions",
    )
    op.drop_index(
        "ix_governance_member_permissions_permission_id",
        table_name="governance_member_permissions",
    )
    op.drop_index(
        "ix_governance_member_permissions_governance_member_id",
        table_name="governance_member_permissions",
    )
    op.drop_index("ix_governance_member_permissions_id", table_name="governance_member_permissions")
    op.drop_table("governance_member_permissions")

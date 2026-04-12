"""Use: Implements the database change for add sanctions governance permissions.
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

add sanctions governance permissions

Revision ID: e2f7a1c9d4b6
Revises: d1a2b3c4d5e6
Create Date: 2026-04-11 23:45:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e2f7a1c9d4b6"
down_revision: Union[str, None] = "d1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BASE_GOVERNANCE_PERMISSION_CODES = (
    "create_sg",
    "create_org",
    "manage_students",
    "view_students",
    "manage_members",
    "manage_events",
    "manage_attendance",
    "manage_announcements",
    "assign_permissions",
)

SANCTIONS_GOVERNANCE_PERMISSION_CODES = (
    "view_sanctioned_students_list",
    "view_student_sanction_detail",
    "approve_sanction_compliance",
    "configure_event_sanctions",
    "export_sanctioned_students",
    "view_sanctions_dashboard",
)

previous_governance_permission_code_enum = sa.Enum(
    *BASE_GOVERNANCE_PERMISSION_CODES,
    name="governance_permission_code",
    native_enum=False,
)
current_governance_permission_code_enum = sa.Enum(
    *(BASE_GOVERNANCE_PERMISSION_CODES + SANCTIONS_GOVERNANCE_PERMISSION_CODES),
    name="governance_permission_code",
    native_enum=False,
)

NEW_PERMISSIONS: tuple[dict[str, str], ...] = (
    {
        "permission_code": "view_sanctioned_students_list",
        "permission_name": "View Sanctioned Students List",
        "description": "Allows members of the unit to view sanctioned students lists for accessible events.",
    },
    {
        "permission_code": "view_student_sanction_detail",
        "permission_name": "View Student Sanction Detail",
        "description": "Allows members of the unit to view detailed sanction records for accessible students.",
    },
    {
        "permission_code": "approve_sanction_compliance",
        "permission_name": "Approve Sanction Compliance",
        "description": "Allows members of the unit to mark student sanctions as complied for accessible events.",
    },
    {
        "permission_code": "configure_event_sanctions",
        "permission_name": "Configure Event Sanctions",
        "description": "Allows members of the unit to configure event sanctions, delegation, and clearance deadline actions.",
    },
    {
        "permission_code": "export_sanctioned_students",
        "permission_name": "Export Sanctioned Students",
        "description": "Allows members of the unit to export sanctioned student records for accessible events.",
    },
    {
        "permission_code": "view_sanctions_dashboard",
        "permission_name": "View Sanctions Dashboard",
        "description": "Allows members of the unit to view sanctions dashboard summaries for accessible events.",
    },
)


def _widen_governance_permission_code_enum() -> None:
    with op.batch_alter_table("governance_permissions", schema=None) as batch_op:
        batch_op.alter_column(
            "permission_code",
            existing_type=previous_governance_permission_code_enum,
            type_=current_governance_permission_code_enum,
            existing_nullable=False,
        )


def _narrow_governance_permission_code_enum() -> None:
    with op.batch_alter_table("governance_permissions", schema=None) as batch_op:
        batch_op.alter_column(
            "permission_code",
            existing_type=current_governance_permission_code_enum,
            type_=previous_governance_permission_code_enum,
            existing_nullable=False,
        )


def upgrade() -> None:
    _widen_governance_permission_code_enum()

    bind = op.get_bind()
    existing_codes = {
        row[0]
        for row in bind.execute(sa.text("SELECT permission_code FROM governance_permissions"))
    }
    rows_to_insert = [row for row in NEW_PERMISSIONS if row["permission_code"] not in existing_codes]
    if not rows_to_insert:
        return

    governance_permissions_table = sa.table(
        "governance_permissions",
        sa.column("permission_code", sa.String(length=64)),
        sa.column("permission_name", sa.String(length=100)),
        sa.column("description", sa.Text()),
    )
    op.bulk_insert(governance_permissions_table, rows_to_insert)


def downgrade() -> None:
    permission_codes_csv = ", ".join(f"'{code}'" for code in SANCTIONS_GOVERNANCE_PERMISSION_CODES)

    op.execute(
        sa.text(
            f"""
            DELETE FROM governance_member_permissions
            WHERE permission_id IN (
                SELECT id FROM governance_permissions
                WHERE permission_code IN ({permission_codes_csv})
            )
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            DELETE FROM governance_unit_permissions
            WHERE permission_id IN (
                SELECT id FROM governance_permissions
                WHERE permission_code IN ({permission_codes_csv})
            )
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            DELETE FROM governance_permissions
            WHERE permission_code IN ({permission_codes_csv})
            """
        )
    )

    _narrow_governance_permission_code_enum()

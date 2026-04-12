"""Use: Implements the database change for add sanctions management tables.
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

add sanctions management tables

Revision ID: d1a2b3c4d5e6
Revises: c6e1f4a8b9d0
Create Date: 2026-04-11 22:15:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d1a2b3c4d5e6"
down_revision: Union[str, None] = "c6e1f4a8b9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


sanction_compliance_status_enum = sa.Enum(
    "pending",
    "complied",
    name="sanction_compliance_status",
    native_enum=False,
)
sanction_item_status_enum = sa.Enum(
    "pending",
    "complied",
    name="sanction_item_status",
    native_enum=False,
)
sanction_delegation_scope_type_enum = sa.Enum(
    "unit",
    "department",
    "program",
    "school",
    name="sanction_delegation_scope_type",
    native_enum=False,
)
clearance_deadline_status_enum = sa.Enum(
    "active",
    "closed",
    "expired",
    name="clearance_deadline_status",
    native_enum=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    sanction_compliance_status_enum.create(bind, checkfirst=True)
    sanction_item_status_enum.create(bind, checkfirst=True)
    sanction_delegation_scope_type_enum.create(bind, checkfirst=True)
    clearance_deadline_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "event_sanction_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("sanctions_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("item_definitions_json", sa.JSON(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_event_sanction_configs_event_id"),
    )
    op.create_index("ix_event_sanction_configs_id", "event_sanction_configs", ["id"], unique=False)
    op.create_index("ix_event_sanction_configs_school_id", "event_sanction_configs", ["school_id"], unique=False)
    op.create_index("ix_event_sanction_configs_event_id", "event_sanction_configs", ["event_id"], unique=False)
    op.create_index(
        "ix_event_sanction_configs_sanctions_enabled",
        "event_sanction_configs",
        ["sanctions_enabled"],
        unique=False,
    )
    op.create_index(
        "ix_event_sanction_configs_created_by_user_id",
        "event_sanction_configs",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_event_sanction_configs_updated_by_user_id",
        "event_sanction_configs",
        ["updated_by_user_id"],
        unique=False,
    )
    op.create_index("ix_event_sanction_configs_created_at", "event_sanction_configs", ["created_at"], unique=False)

    op.create_table(
        "sanction_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("sanction_config_id", sa.Integer(), nullable=True),
        sa.Column("student_profile_id", sa.Integer(), nullable=False),
        sa.Column("attendance_id", sa.Integer(), nullable=True),
        sa.Column("delegated_governance_unit_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sanction_compliance_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=True),
        sa.Column("complied_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sanction_config_id"], ["event_sanction_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["attendance_id"], ["attendances.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["delegated_governance_unit_id"], ["governance_units.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "student_profile_id", name="uq_sanction_records_event_student"),
    )
    op.create_index("ix_sanction_records_id", "sanction_records", ["id"], unique=False)
    op.create_index("ix_sanction_records_school_id", "sanction_records", ["school_id"], unique=False)
    op.create_index("ix_sanction_records_event_id", "sanction_records", ["event_id"], unique=False)
    op.create_index("ix_sanction_records_sanction_config_id", "sanction_records", ["sanction_config_id"], unique=False)
    op.create_index("ix_sanction_records_student_profile_id", "sanction_records", ["student_profile_id"], unique=False)
    op.create_index("ix_sanction_records_attendance_id", "sanction_records", ["attendance_id"], unique=False)
    op.create_index(
        "ix_sanction_records_delegated_governance_unit_id",
        "sanction_records",
        ["delegated_governance_unit_id"],
        unique=False,
    )
    op.create_index("ix_sanction_records_status", "sanction_records", ["status"], unique=False)
    op.create_index("ix_sanction_records_assigned_by_user_id", "sanction_records", ["assigned_by_user_id"], unique=False)
    op.create_index("ix_sanction_records_complied_at", "sanction_records", ["complied_at"], unique=False)
    op.create_index("ix_sanction_records_created_at", "sanction_records", ["created_at"], unique=False)

    op.create_table(
        "sanction_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sanction_record_id", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(length=64), nullable=True),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("item_description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sanction_item_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("complied_at", sa.DateTime(), nullable=True),
        sa.Column("compliance_notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["sanction_record_id"], ["sanction_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sanction_record_id", "item_code", name="uq_sanction_items_record_item_code"),
    )
    op.create_index("ix_sanction_items_id", "sanction_items", ["id"], unique=False)
    op.create_index("ix_sanction_items_sanction_record_id", "sanction_items", ["sanction_record_id"], unique=False)
    op.create_index("ix_sanction_items_item_code", "sanction_items", ["item_code"], unique=False)
    op.create_index("ix_sanction_items_status", "sanction_items", ["status"], unique=False)
    op.create_index("ix_sanction_items_complied_at", "sanction_items", ["complied_at"], unique=False)
    op.create_index("ix_sanction_items_created_at", "sanction_items", ["created_at"], unique=False)

    op.create_table(
        "sanction_delegations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("sanction_config_id", sa.Integer(), nullable=True),
        sa.Column("delegated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("delegated_to_governance_unit_id", sa.Integer(), nullable=False),
        sa.Column(
            "scope_type",
            sanction_delegation_scope_type_enum,
            nullable=False,
            server_default="unit",
        ),
        sa.Column("scope_json", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sanction_config_id"], ["event_sanction_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["delegated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["delegated_to_governance_unit_id"], ["governance_units.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["revoked_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            "delegated_to_governance_unit_id",
            name="uq_sanction_delegations_event_governance_unit",
        ),
    )
    op.create_index("ix_sanction_delegations_id", "sanction_delegations", ["id"], unique=False)
    op.create_index("ix_sanction_delegations_school_id", "sanction_delegations", ["school_id"], unique=False)
    op.create_index("ix_sanction_delegations_event_id", "sanction_delegations", ["event_id"], unique=False)
    op.create_index(
        "ix_sanction_delegations_sanction_config_id",
        "sanction_delegations",
        ["sanction_config_id"],
        unique=False,
    )
    op.create_index(
        "ix_sanction_delegations_delegated_by_user_id",
        "sanction_delegations",
        ["delegated_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_sanction_delegations_delegated_to_governance_unit_id",
        "sanction_delegations",
        ["delegated_to_governance_unit_id"],
        unique=False,
    )
    op.create_index("ix_sanction_delegations_scope_type", "sanction_delegations", ["scope_type"], unique=False)
    op.create_index("ix_sanction_delegations_is_active", "sanction_delegations", ["is_active"], unique=False)
    op.create_index(
        "ix_sanction_delegations_revoked_by_user_id",
        "sanction_delegations",
        ["revoked_by_user_id"],
        unique=False,
    )
    op.create_index("ix_sanction_delegations_created_at", "sanction_delegations", ["created_at"], unique=False)

    op.create_table(
        "sanction_compliance_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("sanction_record_id", sa.Integer(), nullable=True),
        sa.Column("sanction_item_id", sa.Integer(), nullable=True),
        sa.Column("student_profile_id", sa.Integer(), nullable=True),
        sa.Column("complied_on", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("school_year", sa.String(length=20), nullable=False),
        sa.Column("semester", sa.String(length=20), nullable=False),
        sa.Column("complied_by_user_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sanction_record_id"], ["sanction_records.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sanction_item_id"], ["sanction_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["complied_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sanction_compliance_history_id", "sanction_compliance_history", ["id"], unique=False)
    op.create_index("ix_sanction_compliance_history_school_id", "sanction_compliance_history", ["school_id"], unique=False)
    op.create_index("ix_sanction_compliance_history_event_id", "sanction_compliance_history", ["event_id"], unique=False)
    op.create_index(
        "ix_sanction_compliance_history_sanction_record_id",
        "sanction_compliance_history",
        ["sanction_record_id"],
        unique=False,
    )
    op.create_index(
        "ix_sanction_compliance_history_sanction_item_id",
        "sanction_compliance_history",
        ["sanction_item_id"],
        unique=False,
    )
    op.create_index(
        "ix_sanction_compliance_history_student_profile_id",
        "sanction_compliance_history",
        ["student_profile_id"],
        unique=False,
    )
    op.create_index(
        "ix_sanction_compliance_history_complied_by_user_id",
        "sanction_compliance_history",
        ["complied_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_sanction_compliance_history_complied_on",
        "sanction_compliance_history",
        ["complied_on"],
        unique=False,
    )
    op.create_index(
        "ix_sanction_compliance_history_school_year",
        "sanction_compliance_history",
        ["school_year"],
        unique=False,
    )
    op.create_index(
        "ix_sanction_compliance_history_semester",
        "sanction_compliance_history",
        ["semester"],
        unique=False,
    )
    op.create_index(
        "ix_sanction_compliance_history_created_at",
        "sanction_compliance_history",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "clearance_deadlines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("declared_by_user_id", sa.Integer(), nullable=True),
        sa.Column("target_governance_unit_id", sa.Integer(), nullable=True),
        sa.Column("deadline_at", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            clearance_deadline_status_enum,
            nullable=False,
            server_default="active",
        ),
        sa.Column("warning_email_sent_at", sa.DateTime(), nullable=True),
        sa.Column("warning_popup_sent_at", sa.DateTime(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["declared_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_governance_unit_id"], ["governance_units.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clearance_deadlines_id", "clearance_deadlines", ["id"], unique=False)
    op.create_index("ix_clearance_deadlines_school_id", "clearance_deadlines", ["school_id"], unique=False)
    op.create_index("ix_clearance_deadlines_event_id", "clearance_deadlines", ["event_id"], unique=False)
    op.create_index(
        "ix_clearance_deadlines_declared_by_user_id",
        "clearance_deadlines",
        ["declared_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_clearance_deadlines_target_governance_unit_id",
        "clearance_deadlines",
        ["target_governance_unit_id"],
        unique=False,
    )
    op.create_index("ix_clearance_deadlines_deadline_at", "clearance_deadlines", ["deadline_at"], unique=False)
    op.create_index("ix_clearance_deadlines_status", "clearance_deadlines", ["status"], unique=False)
    op.create_index("ix_clearance_deadlines_created_at", "clearance_deadlines", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_clearance_deadlines_created_at", table_name="clearance_deadlines")
    op.drop_index("ix_clearance_deadlines_status", table_name="clearance_deadlines")
    op.drop_index("ix_clearance_deadlines_deadline_at", table_name="clearance_deadlines")
    op.drop_index("ix_clearance_deadlines_target_governance_unit_id", table_name="clearance_deadlines")
    op.drop_index("ix_clearance_deadlines_declared_by_user_id", table_name="clearance_deadlines")
    op.drop_index("ix_clearance_deadlines_event_id", table_name="clearance_deadlines")
    op.drop_index("ix_clearance_deadlines_school_id", table_name="clearance_deadlines")
    op.drop_index("ix_clearance_deadlines_id", table_name="clearance_deadlines")
    op.drop_table("clearance_deadlines")

    op.drop_index("ix_sanction_compliance_history_created_at", table_name="sanction_compliance_history")
    op.drop_index("ix_sanction_compliance_history_semester", table_name="sanction_compliance_history")
    op.drop_index("ix_sanction_compliance_history_school_year", table_name="sanction_compliance_history")
    op.drop_index("ix_sanction_compliance_history_complied_on", table_name="sanction_compliance_history")
    op.drop_index("ix_sanction_compliance_history_complied_by_user_id", table_name="sanction_compliance_history")
    op.drop_index("ix_sanction_compliance_history_student_profile_id", table_name="sanction_compliance_history")
    op.drop_index("ix_sanction_compliance_history_sanction_item_id", table_name="sanction_compliance_history")
    op.drop_index("ix_sanction_compliance_history_sanction_record_id", table_name="sanction_compliance_history")
    op.drop_index("ix_sanction_compliance_history_event_id", table_name="sanction_compliance_history")
    op.drop_index("ix_sanction_compliance_history_school_id", table_name="sanction_compliance_history")
    op.drop_index("ix_sanction_compliance_history_id", table_name="sanction_compliance_history")
    op.drop_table("sanction_compliance_history")

    op.drop_index("ix_sanction_delegations_created_at", table_name="sanction_delegations")
    op.drop_index("ix_sanction_delegations_revoked_by_user_id", table_name="sanction_delegations")
    op.drop_index("ix_sanction_delegations_is_active", table_name="sanction_delegations")
    op.drop_index("ix_sanction_delegations_scope_type", table_name="sanction_delegations")
    op.drop_index("ix_sanction_delegations_delegated_to_governance_unit_id", table_name="sanction_delegations")
    op.drop_index("ix_sanction_delegations_delegated_by_user_id", table_name="sanction_delegations")
    op.drop_index("ix_sanction_delegations_sanction_config_id", table_name="sanction_delegations")
    op.drop_index("ix_sanction_delegations_event_id", table_name="sanction_delegations")
    op.drop_index("ix_sanction_delegations_school_id", table_name="sanction_delegations")
    op.drop_index("ix_sanction_delegations_id", table_name="sanction_delegations")
    op.drop_table("sanction_delegations")

    op.drop_index("ix_sanction_items_created_at", table_name="sanction_items")
    op.drop_index("ix_sanction_items_complied_at", table_name="sanction_items")
    op.drop_index("ix_sanction_items_status", table_name="sanction_items")
    op.drop_index("ix_sanction_items_item_code", table_name="sanction_items")
    op.drop_index("ix_sanction_items_sanction_record_id", table_name="sanction_items")
    op.drop_index("ix_sanction_items_id", table_name="sanction_items")
    op.drop_table("sanction_items")

    op.drop_index("ix_sanction_records_created_at", table_name="sanction_records")
    op.drop_index("ix_sanction_records_complied_at", table_name="sanction_records")
    op.drop_index("ix_sanction_records_assigned_by_user_id", table_name="sanction_records")
    op.drop_index("ix_sanction_records_status", table_name="sanction_records")
    op.drop_index("ix_sanction_records_delegated_governance_unit_id", table_name="sanction_records")
    op.drop_index("ix_sanction_records_attendance_id", table_name="sanction_records")
    op.drop_index("ix_sanction_records_student_profile_id", table_name="sanction_records")
    op.drop_index("ix_sanction_records_sanction_config_id", table_name="sanction_records")
    op.drop_index("ix_sanction_records_event_id", table_name="sanction_records")
    op.drop_index("ix_sanction_records_school_id", table_name="sanction_records")
    op.drop_index("ix_sanction_records_id", table_name="sanction_records")
    op.drop_table("sanction_records")

    op.drop_index("ix_event_sanction_configs_created_at", table_name="event_sanction_configs")
    op.drop_index("ix_event_sanction_configs_updated_by_user_id", table_name="event_sanction_configs")
    op.drop_index("ix_event_sanction_configs_created_by_user_id", table_name="event_sanction_configs")
    op.drop_index("ix_event_sanction_configs_sanctions_enabled", table_name="event_sanction_configs")
    op.drop_index("ix_event_sanction_configs_event_id", table_name="event_sanction_configs")
    op.drop_index("ix_event_sanction_configs_school_id", table_name="event_sanction_configs")
    op.drop_index("ix_event_sanction_configs_id", table_name="event_sanction_configs")
    op.drop_table("event_sanction_configs")

    bind = op.get_bind()
    clearance_deadline_status_enum.drop(bind, checkfirst=True)
    sanction_delegation_scope_type_enum.drop(bind, checkfirst=True)
    sanction_item_status_enum.drop(bind, checkfirst=True)
    sanction_compliance_status_enum.drop(bind, checkfirst=True)

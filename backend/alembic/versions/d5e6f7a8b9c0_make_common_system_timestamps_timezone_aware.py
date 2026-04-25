"""Make common system timestamps timezone-aware UTC.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-04-25 15:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


SYSTEM_TIMESTAMP_COLUMNS = {
    "users": ["created_at"],
    "student_profiles": ["last_face_update"],
    "schools": ["created_at", "updated_at"],
    "school_settings": ["updated_at"],
    "school_audit_logs": ["created_at"],
    "user_notification_preferences": ["updated_at"],
    "user_app_preferences": ["updated_at"],
    "notification_logs": ["created_at"],
    "user_security_settings": ["updated_at"],
    "user_face_profiles": ["last_verified_at", "created_at", "updated_at"],
    "mfa_challenges": ["expires_at", "consumed_at", "created_at"],
    "user_sessions": ["created_at", "last_seen_at", "revoked_at", "expires_at"],
    "login_history": ["created_at"],
    "school_subscription_settings": ["updated_at"],
    "school_subscription_reminders": ["due_at", "sent_at", "created_at"],
    "data_governance_settings": ["updated_at"],
    "user_privacy_consents": ["created_at"],
    "data_requests": ["created_at", "resolved_at"],
    "data_retention_run_logs": ["created_at"],
    "governance_units": ["created_at", "updated_at"],
    "governance_members": ["assigned_at"],
    "governance_unit_permissions": ["created_at"],
    "governance_member_permissions": ["created_at"],
    "governance_announcements": ["created_at", "updated_at"],
    "governance_student_notes": ["created_at", "updated_at"],
    "bulk_import_jobs": ["started_at", "completed_at", "created_at", "updated_at", "last_heartbeat"],
    "bulk_import_errors": ["created_at"],
    "email_delivery_logs": ["created_at", "updated_at"],
    "password_reset_requests": ["requested_at", "resolved_at"],
    "event_types": ["created_at", "updated_at"],
    "event_sanction_configs": ["created_at", "updated_at"],
    "sanction_records": ["complied_at", "created_at", "updated_at"],
    "sanction_items": ["complied_at", "created_at", "updated_at"],
    "sanction_delegations": ["revoked_at", "created_at", "updated_at"],
    "sanction_compliance_history": ["created_at"],
    "clearance_deadlines": [
        "deadline_at",
        "warning_email_sent_at",
        "warning_popup_sent_at",
        "created_at",
        "updated_at",
    ],
}


def _drop_dependent_views() -> None:
    op.execute("DROP VIEW IF EXISTS user_count_by_school")
    op.execute("DROP VIEW IF EXISTS user_by_schools")


def _recreate_dependent_views() -> None:
    op.execute(
        """
        CREATE VIEW user_by_schools AS
        SELECT
            s.id AS school_id,
            s.school_name,
            s.school_code,
            s.active_status,
            s.subscription_status,
            u.id AS user_id,
            u.email,
            u.first_name,
            u.middle_name,
            u.last_name,
            u.is_active AS user_active,
            u.created_at AS user_created_at,
            r.name AS role,
            CASE
                WHEN sp.id IS NOT NULL THEN true
                ELSE false
            END AS is_student,
            sp.student_id,
            sp.is_face_registered
        FROM schools s
        LEFT JOIN users u ON s.id = u.school_id
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        ORDER BY s.id, u.id
        """
    )
    op.execute(
        """
        CREATE VIEW user_count_by_school AS
        SELECT
            s.id AS school_id,
            s.school_name,
            s.school_code,
            s.active_status,
            s.subscription_status,
            count(u.id) AS total_users,
            count(CASE WHEN r.name = 'student' THEN 1 ELSE NULL END) AS total_students,
            count(CASE WHEN r.name = 'campus_admin' THEN 1 ELSE NULL END) AS total_campus_admins,
            count(CASE WHEN r.name = 'teacher' THEN 1 ELSE NULL END) AS total_teachers,
            count(CASE WHEN sp.is_face_registered = true THEN 1 ELSE NULL END) AS students_with_face
        FROM schools s
        LEFT JOIN users u ON s.id = u.school_id
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        GROUP BY
            s.id,
            s.school_name,
            s.school_code,
            s.active_status,
            s.subscription_status
        ORDER BY s.id
        """
    )


def _alter_table_timestamps(table_name: str, columns: list[str], *, timezone_clause: str) -> None:
    clauses = [
        f"ALTER COLUMN {column_name} TYPE TIMESTAMP {timezone_clause} USING {column_name} AT TIME ZONE 'UTC'"
        for column_name in columns
    ]
    op.execute(
        f"""
        ALTER TABLE {table_name}
        {", ".join(clauses)}
        """
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    _drop_dependent_views()
    for table_name, columns in SYSTEM_TIMESTAMP_COLUMNS.items():
        if table_name in existing_tables:
            _alter_table_timestamps(table_name, columns, timezone_clause="WITH TIME ZONE")
    if "schools" in existing_tables and "users" in existing_tables:
        _recreate_dependent_views()


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    _drop_dependent_views()
    for table_name, columns in SYSTEM_TIMESTAMP_COLUMNS.items():
        if table_name in existing_tables:
            _alter_table_timestamps(table_name, columns, timezone_clause="WITHOUT TIME ZONE")
    if "schools" in existing_tables and "users" in existing_tables:
        _recreate_dependent_views()

"""add platform ops, security, notifications, subscription and governance tables

Revision ID: c3d4e5f6a7b8
Revises: b7f8c9d0e1f2
Create Date: 2026-03-06 19:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b7f8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_notification_preferences",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sms_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sms_number", sa.String(length=40), nullable=True),
        sa.Column("notify_missed_events", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_low_attendance", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_account_security", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_subscription", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="email"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_logs_school_id", "notification_logs", ["school_id"], unique=False)
    op.create_index("ix_notification_logs_user_id", "notification_logs", ["user_id"], unique=False)
    op.create_index("ix_notification_logs_category", "notification_logs", ["category"], unique=False)
    op.create_index("ix_notification_logs_status", "notification_logs", ["status"], unique=False)
    op.create_index("ix_notification_logs_created_at", "notification_logs", ["created_at"], unique=False)

    op.create_table(
        "user_security_settings",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("trusted_device_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "mfa_challenges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="email"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mfa_challenges_user_id", "mfa_challenges", ["user_id"], unique=False)
    op.create_index("ix_mfa_challenges_expires_at", "mfa_challenges", ["expires_at"], unique=False)
    op.create_index("ix_mfa_challenges_created_at", "mfa_challenges", ["created_at"], unique=False)

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_jti", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"], unique=False)
    op.create_index("ix_user_sessions_token_jti", "user_sessions", ["token_jti"], unique=True)
    op.create_index("ix_user_sessions_created_at", "user_sessions", ["created_at"], unique=False)
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"], unique=False)

    op.create_table(
        "login_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("email_attempted", sa.String(length=255), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("auth_method", sa.String(length=30), nullable=False, server_default="password"),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_login_history_user_id", "login_history", ["user_id"], unique=False)
    op.create_index("ix_login_history_school_id", "login_history", ["school_id"], unique=False)
    op.create_index("ix_login_history_email_attempted", "login_history", ["email_attempted"], unique=False)
    op.create_index("ix_login_history_success", "login_history", ["success"], unique=False)
    op.create_index("ix_login_history_created_at", "login_history", ["created_at"], unique=False)

    op.create_table(
        "school_subscription_settings",
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("plan_name", sa.String(length=50), nullable=False, server_default="free"),
        sa.Column("user_limit", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("event_limit_monthly", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("import_limit_monthly", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reminder_days_before", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("school_id"),
    )

    op.execute(
        """
        INSERT INTO school_subscription_settings (school_id, plan_name, user_limit, event_limit_monthly, import_limit_monthly, renewal_date, auto_renew, reminder_days_before)
        SELECT id, COALESCE(subscription_plan, 'free'), 500, 100, 10, subscription_end, FALSE, 14
        FROM schools
        WHERE NOT EXISTS (
            SELECT 1 FROM school_subscription_settings sss WHERE sss.school_id = schools.id
        )
        """
    )

    op.create_table(
        "school_subscription_reminders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("reminder_type", sa.String(length=40), nullable=False, server_default="renewal_warning"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("due_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_school_subscription_reminders_school_id", "school_subscription_reminders", ["school_id"], unique=False)
    op.create_index("ix_school_subscription_reminders_status", "school_subscription_reminders", ["status"], unique=False)
    op.create_index("ix_school_subscription_reminders_due_at", "school_subscription_reminders", ["due_at"], unique=False)

    op.create_table(
        "data_governance_settings",
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("attendance_retention_days", sa.Integer(), nullable=False, server_default="1095"),
        sa.Column("audit_log_retention_days", sa.Integer(), nullable=False, server_default="3650"),
        sa.Column("import_file_retention_days", sa.Integer(), nullable=False, server_default="180"),
        sa.Column("auto_delete_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("school_id"),
    )

    op.execute(
        """
        INSERT INTO data_governance_settings (school_id, attendance_retention_days, audit_log_retention_days, import_file_retention_days, auto_delete_enabled)
        SELECT id, 1095, 3650, 180, FALSE
        FROM schools
        WHERE NOT EXISTS (
            SELECT 1 FROM data_governance_settings dgs WHERE dgs.school_id = schools.id
        )
        """
    )

    op.create_table(
        "user_privacy_consents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("consent_type", sa.String(length=50), nullable=False),
        sa.Column("consent_granted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("consent_version", sa.String(length=20), nullable=False, server_default="v1"),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="web"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_privacy_consents_user_id", "user_privacy_consents", ["user_id"], unique=False)
    op.create_index("ix_user_privacy_consents_school_id", "user_privacy_consents", ["school_id"], unique=False)
    op.create_index("ix_user_privacy_consents_consent_type", "user_privacy_consents", ["consent_type"], unique=False)
    op.create_index("ix_user_privacy_consents_created_at", "user_privacy_consents", ["created_at"], unique=False)

    op.create_table(
        "data_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("request_type", sa.String(length=20), nullable=False),
        sa.Column("scope", sa.String(length=50), nullable=False, server_default="user_data"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("output_path", sa.String(length=1024), nullable=True),
        sa.Column("handled_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["handled_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_requests_school_id", "data_requests", ["school_id"], unique=False)
    op.create_index("ix_data_requests_requested_by_user_id", "data_requests", ["requested_by_user_id"], unique=False)
    op.create_index("ix_data_requests_target_user_id", "data_requests", ["target_user_id"], unique=False)
    op.create_index("ix_data_requests_request_type", "data_requests", ["request_type"], unique=False)
    op.create_index("ix_data_requests_status", "data_requests", ["status"], unique=False)
    op.create_index("ix_data_requests_created_at", "data_requests", ["created_at"], unique=False)

    op.create_table(
        "data_retention_run_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_retention_run_logs_school_id", "data_retention_run_logs", ["school_id"], unique=False)
    op.create_index("ix_data_retention_run_logs_created_at", "data_retention_run_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_data_retention_run_logs_created_at", table_name="data_retention_run_logs")
    op.drop_index("ix_data_retention_run_logs_school_id", table_name="data_retention_run_logs")
    op.drop_table("data_retention_run_logs")

    op.drop_index("ix_data_requests_created_at", table_name="data_requests")
    op.drop_index("ix_data_requests_status", table_name="data_requests")
    op.drop_index("ix_data_requests_request_type", table_name="data_requests")
    op.drop_index("ix_data_requests_target_user_id", table_name="data_requests")
    op.drop_index("ix_data_requests_requested_by_user_id", table_name="data_requests")
    op.drop_index("ix_data_requests_school_id", table_name="data_requests")
    op.drop_table("data_requests")

    op.drop_index("ix_user_privacy_consents_created_at", table_name="user_privacy_consents")
    op.drop_index("ix_user_privacy_consents_consent_type", table_name="user_privacy_consents")
    op.drop_index("ix_user_privacy_consents_school_id", table_name="user_privacy_consents")
    op.drop_index("ix_user_privacy_consents_user_id", table_name="user_privacy_consents")
    op.drop_table("user_privacy_consents")

    op.drop_table("data_governance_settings")

    op.drop_index("ix_school_subscription_reminders_due_at", table_name="school_subscription_reminders")
    op.drop_index("ix_school_subscription_reminders_status", table_name="school_subscription_reminders")
    op.drop_index("ix_school_subscription_reminders_school_id", table_name="school_subscription_reminders")
    op.drop_table("school_subscription_reminders")

    op.drop_table("school_subscription_settings")

    op.drop_index("ix_login_history_created_at", table_name="login_history")
    op.drop_index("ix_login_history_success", table_name="login_history")
    op.drop_index("ix_login_history_email_attempted", table_name="login_history")
    op.drop_index("ix_login_history_school_id", table_name="login_history")
    op.drop_index("ix_login_history_user_id", table_name="login_history")
    op.drop_table("login_history")

    op.drop_index("ix_user_sessions_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_created_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_token_jti", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_index("ix_mfa_challenges_created_at", table_name="mfa_challenges")
    op.drop_index("ix_mfa_challenges_expires_at", table_name="mfa_challenges")
    op.drop_index("ix_mfa_challenges_user_id", table_name="mfa_challenges")
    op.drop_table("mfa_challenges")

    op.drop_table("user_security_settings")

    op.drop_index("ix_notification_logs_created_at", table_name="notification_logs")
    op.drop_index("ix_notification_logs_status", table_name="notification_logs")
    op.drop_index("ix_notification_logs_category", table_name="notification_logs")
    op.drop_index("ix_notification_logs_user_id", table_name="notification_logs")
    op.drop_index("ix_notification_logs_school_id", table_name="notification_logs")
    op.drop_table("notification_logs")

    op.drop_table("user_notification_preferences")

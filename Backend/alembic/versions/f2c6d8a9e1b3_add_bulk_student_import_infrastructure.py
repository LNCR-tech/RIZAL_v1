"""add_bulk_student_import_infrastructure

Revision ID: f2c6d8a9e1b3
Revises: d8a0b2d7f8c1
Create Date: 2026-03-04 09:05:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2c6d8a9e1b3"
down_revision: Union[str, None] = "d8a0b2d7f8c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.execute("UPDATE users SET must_change_password = FALSE")

    op.add_column("student_profiles", sa.Column("school_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_student_profiles_school_id_schools",
        "student_profiles",
        "schools",
        ["school_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.execute(
        """
        UPDATE student_profiles sp
        SET school_id = u.school_id
        FROM users u
        WHERE sp.user_id = u.id
        """
    )

    op.alter_column("student_profiles", "school_id", nullable=False)

    op.execute("ALTER TABLE student_profiles DROP CONSTRAINT IF EXISTS student_profiles_student_id_key")

    op.create_unique_constraint(
        "uq_student_profiles_school_student_id",
        "student_profiles",
        ["school_id", "student_id"],
    )

    op.create_index("ix_student_profiles_school_id", "student_profiles", ["school_id"], unique=False)
    op.create_index(
        "ix_student_profiles_school_student_id",
        "student_profiles",
        ["school_id", "student_id"],
        unique=False,
    )

    op.create_table(
        "bulk_import_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_file_path", sa.String(length=1024), nullable=False),
        sa.Column("failed_report_path", sa.String(length=1024), nullable=True),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("eta_seconds", sa.Integer(), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("is_rate_limited", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_heartbeat", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bulk_import_jobs_status", "bulk_import_jobs", ["status"], unique=False)
    op.create_index("ix_bulk_import_jobs_created_at", "bulk_import_jobs", ["created_at"], unique=False)
    op.create_index("ix_bulk_import_jobs_created_by_user_id", "bulk_import_jobs", ["created_by_user_id"], unique=False)

    op.create_table(
        "bulk_import_errors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("row_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["job_id"], ["bulk_import_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bulk_import_errors_job_id", "bulk_import_errors", ["job_id"], unique=False)
    op.create_index(
        "ix_bulk_import_errors_job_row",
        "bulk_import_errors",
        ["job_id", "row_number"],
        unique=False,
    )

    op.create_table(
        "email_delivery_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["job_id"], ["bulk_import_jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_delivery_logs_job_id", "email_delivery_logs", ["job_id"], unique=False)
    op.create_index("ix_email_delivery_logs_user_id", "email_delivery_logs", ["user_id"], unique=False)
    op.create_index("ix_email_delivery_logs_email", "email_delivery_logs", ["email"], unique=False)
    op.create_index("ix_email_delivery_logs_status", "email_delivery_logs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_email_delivery_logs_status", table_name="email_delivery_logs")
    op.drop_index("ix_email_delivery_logs_email", table_name="email_delivery_logs")
    op.drop_index("ix_email_delivery_logs_user_id", table_name="email_delivery_logs")
    op.drop_index("ix_email_delivery_logs_job_id", table_name="email_delivery_logs")
    op.drop_table("email_delivery_logs")

    op.drop_index("ix_bulk_import_errors_job_row", table_name="bulk_import_errors")
    op.drop_index("ix_bulk_import_errors_job_id", table_name="bulk_import_errors")
    op.drop_table("bulk_import_errors")

    op.drop_index("ix_bulk_import_jobs_created_by_user_id", table_name="bulk_import_jobs")
    op.drop_index("ix_bulk_import_jobs_created_at", table_name="bulk_import_jobs")
    op.drop_index("ix_bulk_import_jobs_status", table_name="bulk_import_jobs")
    op.drop_table("bulk_import_jobs")

    op.drop_index("ix_student_profiles_school_student_id", table_name="student_profiles")
    op.drop_index("ix_student_profiles_school_id", table_name="student_profiles")
    op.drop_constraint("uq_student_profiles_school_student_id", "student_profiles", type_="unique")

    op.drop_constraint("fk_student_profiles_school_id_schools", "student_profiles", type_="foreignkey")
    op.drop_column("student_profiles", "school_id")

    op.drop_column("users", "must_change_password")

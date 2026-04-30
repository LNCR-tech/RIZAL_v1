"""add issue_reports, user_feedbacks, lookup tables, and user age gender columns

Revision ID: 0002_reports_user_demographics
Revises: 0001_baseline
Create Date: 2026-04-30 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_reports_user_demographics"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

_ISSUE_REPORT_TYPES = [
    ("bug", "Bug"),
    ("data_error", "Data Error"),
    ("access_issue", "Access Issue"),
    ("performance", "Performance"),
    ("other", "Other"),
]

_FEEDBACK_CATEGORIES = [
    ("ui", "User Interface"),
    ("performance", "Performance"),
    ("feature_request", "Feature Request"),
    ("general", "General"),
    ("other", "Other"),
]


def upgrade() -> None:
    op.add_column("users", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("gender", sa.Text(), nullable=True))

    op.create_table(
        "issue_report_types",
        sa.Column("code", sa.Text(), primary_key=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "feedback_categories",
        sa.Column("code", sa.Text(), primary_key=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "issue_reports",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("created_by_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reported_by", sa.Text(), nullable=False),
        sa.Column("report_type_code", sa.Text(), sa.ForeignKey("issue_report_types.code", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="open"),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "user_feedbacks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category_code", sa.Text(), sa.ForeignKey("feedback_categories.code", ondelete="RESTRICT"), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Seed lookup tables
    op.bulk_insert(
        sa.table("issue_report_types",
            sa.column("code", sa.Text),
            sa.column("label", sa.Text),
            sa.column("sort_order", sa.Integer),
        ),
        [{"code": code, "label": label, "sort_order": i} for i, (code, label) in enumerate(_ISSUE_REPORT_TYPES)],
    )

    op.bulk_insert(
        sa.table("feedback_categories",
            sa.column("code", sa.Text),
            sa.column("label", sa.Text),
            sa.column("sort_order", sa.Integer),
        ),
        [{"code": code, "label": label, "sort_order": i} for i, (code, label) in enumerate(_FEEDBACK_CATEGORIES)],
    )


def downgrade() -> None:
    op.drop_table("user_feedbacks")
    op.drop_table("issue_reports")
    op.drop_table("feedback_categories")
    op.drop_table("issue_report_types")
    op.drop_column("users", "gender")
    op.drop_column("users", "age")

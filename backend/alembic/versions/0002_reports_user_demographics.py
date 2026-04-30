"""add issue_reports, user_feedbacks tables and user age gender columns

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


def upgrade() -> None:
    op.add_column("users", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("gender", sa.Text(), nullable=True))

    op.create_table(
        "issue_reports",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("created_by_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reported_by", sa.Text(), nullable=False),  # user email or "assistant"
        sa.Column("report_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="open"),  # open, in_progress, resolved, closed
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "user_feedbacks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),  # e.g. ui, performance, feature_request
        sa.Column("rating", sa.Integer(), nullable=True),  # 1-5
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("user_feedbacks")
    op.drop_table("issue_reports")
    op.drop_column("users", "gender")
    op.drop_column("users", "age")

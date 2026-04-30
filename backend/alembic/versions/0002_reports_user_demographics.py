"""add reports table and user age gender columns

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
        "reports",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("created_by_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("report_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("parameters", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("result_data", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_column("users", "gender")
    op.drop_column("users", "age")

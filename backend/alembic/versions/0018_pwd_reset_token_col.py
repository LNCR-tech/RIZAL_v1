"""Add reset_token column to password_reset_tokens for two-step reset flow.

Revision ID: 0018_pwd_reset_token_col
Revises: 0017_gov_ann_school_id
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0018_pwd_reset_token_col"
down_revision = "0017_gov_ann_school_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "password_reset_tokens",
        sa.Column("reset_token", sa.Text(), nullable=True, unique=True),
    )


def downgrade() -> None:
    op.drop_column("password_reset_tokens", "reset_token")

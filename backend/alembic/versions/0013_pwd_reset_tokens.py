"""Add password_reset_tokens table for self-service forgot-password flow.

Revision ID: 0013_pwd_reset_tokens
Revises: 0012_school_ep_face_flags
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0013_pwd_reset_tokens"
down_revision = "0012_school_ep_face_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("password_reset_tokens")

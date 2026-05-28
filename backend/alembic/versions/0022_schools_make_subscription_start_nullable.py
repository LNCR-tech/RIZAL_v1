"""Make legacy schools.subscription_start nullable.

The ORM replaced the column-level subscription fields with a
SchoolSubscription relation. The old columns (subscription_start,
subscription_status, subscription_plan, logo_url) still exist in
the live DB.  subscription_status and subscription_plan have DB-level
defaults so they never caused errors.  subscription_start has no
default → every new school INSERT raises NotNullViolation.

This migration makes subscription_start nullable so the INSERT succeeds
while the old column stays in place for any legacy read queries.

Revision ID: 0022
Revises: 0021
Create Date: 2026-05-28
"""

from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("schools", "subscription_start", nullable=True)


def downgrade() -> None:
    # Backfill so we can restore NOT NULL
    op.execute("""
        UPDATE schools
        SET subscription_start = created_at::date
        WHERE subscription_start IS NULL
    """)
    op.alter_column("schools", "subscription_start", nullable=False)

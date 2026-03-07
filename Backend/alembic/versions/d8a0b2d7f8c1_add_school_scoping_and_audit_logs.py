"""add_school_scoping_and_audit_logs

Revision ID: d8a0b2d7f8c1
Revises: c91e5e67d3f2
Create Date: 2026-03-04 08:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d8a0b2d7f8c1"
down_revision: Union[str, None] = "c91e5e67d3f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure at least one school exists before assigning school_id.
    op.execute(
        """
        INSERT INTO schools (name, address, subscription_plan, subscription_start)
        SELECT 'Default School', 'Default Address', 'free', CURRENT_DATE
        WHERE NOT EXISTS (SELECT 1 FROM schools)
        """
    )

    op.add_column("users", sa.Column("school_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_school_id_schools",
        "users",
        "schools",
        ["school_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_users_school_id", "users", ["school_id"], unique=False)

    op.execute(
        """
        UPDATE users
        SET school_id = (SELECT id FROM schools ORDER BY id ASC LIMIT 1)
        WHERE school_id IS NULL
        """
    )
    op.alter_column("users", "school_id", nullable=False)

    op.add_column("events", sa.Column("school_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_events_school_id_schools",
        "events",
        "schools",
        ["school_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_events_school_id", "events", ["school_id"], unique=False)

    op.execute(
        """
        UPDATE events
        SET school_id = (SELECT id FROM schools ORDER BY id ASC LIMIT 1)
        WHERE school_id IS NULL
        """
    )
    op.alter_column("events", "school_id", nullable=False)

    op.create_table(
        "school_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="success"),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_school_audit_logs_school_id", "school_audit_logs", ["school_id"], unique=False)
    op.create_index("ix_school_audit_logs_actor_user_id", "school_audit_logs", ["actor_user_id"], unique=False)
    op.create_index("ix_school_audit_logs_created_at", "school_audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_school_audit_logs_created_at", table_name="school_audit_logs")
    op.drop_index("ix_school_audit_logs_actor_user_id", table_name="school_audit_logs")
    op.drop_index("ix_school_audit_logs_school_id", table_name="school_audit_logs")
    op.drop_table("school_audit_logs")

    op.drop_index("ix_events_school_id", table_name="events")
    op.drop_constraint("fk_events_school_id_schools", "events", type_="foreignkey")
    op.drop_column("events", "school_id")

    op.drop_index("ix_users_school_id", table_name="users")
    op.drop_constraint("fk_users_school_id_schools", "users", type_="foreignkey")
    op.drop_column("users", "school_id")

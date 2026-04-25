"""add event create idempotency fields

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-04-25 18:45:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "events" not in inspector.get_table_names():
        return
    event_columns = {column["name"] for column in inspector.get_columns("events")}
    event_indexes = {index["name"] for index in inspector.get_indexes("events")}
    event_fks = {foreign_key["name"] for foreign_key in inspector.get_foreign_keys("events")}
    event_unique_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("events")
    }

    if "created_by_user_id" not in event_columns:
        op.add_column("events", sa.Column("created_by_user_id", sa.Integer(), nullable=True))

    if "create_idempotency_key" not in event_columns:
        op.add_column("events", sa.Column("create_idempotency_key", sa.String(length=128), nullable=True))

    if "ix_events_created_by_user_id" not in event_indexes:
        op.create_index("ix_events_created_by_user_id", "events", ["created_by_user_id"], unique=False)

    if "fk_events_created_by_user_id_users" not in event_fks:
        op.create_foreign_key(
            "fk_events_created_by_user_id_users",
            "events",
            "users",
            ["created_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if "uq_events_creator_idempotency_key" not in event_unique_constraints:
        op.create_unique_constraint(
            "uq_events_creator_idempotency_key",
            "events",
            ["created_by_user_id", "create_idempotency_key"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "events" not in inspector.get_table_names():
        return
    event_columns = {column["name"] for column in inspector.get_columns("events")}
    event_indexes = {index["name"] for index in inspector.get_indexes("events")}
    event_fks = {foreign_key["name"] for foreign_key in inspector.get_foreign_keys("events")}
    event_unique_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("events")
    }

    if "uq_events_creator_idempotency_key" in event_unique_constraints:
        op.drop_constraint("uq_events_creator_idempotency_key", "events", type_="unique")

    if "fk_events_created_by_user_id_users" in event_fks:
        op.drop_constraint("fk_events_created_by_user_id_users", "events", type_="foreignkey")

    if "ix_events_created_by_user_id" in event_indexes:
        op.drop_index("ix_events_created_by_user_id", table_name="events")

    if "create_idempotency_key" in event_columns:
        op.drop_column("events", "create_idempotency_key")

    if "created_by_user_id" in event_columns:
        op.drop_column("events", "created_by_user_id")

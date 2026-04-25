"""add event types table and event_type_id relation

Revision ID: 7d43d19e7a58
Revises: e79235331d71
Create Date: 2026-04-25 00:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7d43d19e7a58"
down_revision = "e79235331d71"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    event_columns = (
        {column["name"] for column in inspector.get_columns("events")}
        if "events" in existing_tables
        else set()
    )

    op.create_table(
        "event_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "name", name="uq_event_types_school_name"),
    )
    op.create_index(op.f("ix_event_types_id"), "event_types", ["id"], unique=False)
    op.create_index(op.f("ix_event_types_school_id"), "event_types", ["school_id"], unique=False)

    if "events" not in existing_tables:
        op.alter_column("event_types", "is_active", server_default=None)
        op.alter_column("event_types", "sort_order", server_default=None)
        op.alter_column("event_types", "created_at", server_default=None)
        op.alter_column("event_types", "updated_at", server_default=None)
        return

    if "event_type_id" not in event_columns:
        op.add_column("events", sa.Column("event_type_id", sa.Integer(), nullable=True))
        op.create_index(op.f("ix_events_event_type_id"), "events", ["event_type_id"], unique=False)
        op.create_foreign_key(
            "fk_events_event_type_id_event_types",
            "events",
            "event_types",
            ["event_type_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if "event_type" in event_columns:
        op.execute(
            """
            INSERT INTO event_types (school_id, name, code, description, is_active, sort_order, created_at, updated_at)
            SELECT DISTINCT
                e.school_id,
                BTRIM(e.event_type),
                NULL,
                NULL,
                TRUE,
                0,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            FROM events AS e
            WHERE e.event_type IS NOT NULL
              AND BTRIM(e.event_type) <> ''
              AND NOT EXISTS (
                  SELECT 1
                  FROM event_types AS et
                  WHERE et.school_id = e.school_id
                    AND et.name = BTRIM(e.event_type)
              )
            """
        )

        op.execute(
            """
            UPDATE events AS e
            SET event_type_id = et.id
            FROM event_types AS et
            WHERE et.school_id = e.school_id
              AND et.name = BTRIM(e.event_type)
              AND (e.event_type_id IS NULL)
            """
        )

        op.execute(
            """
            INSERT INTO event_types (school_id, name, code, description, is_active, sort_order, created_at, updated_at)
            SELECT
                NULL,
                'Regular Event',
                'regular-event',
                NULL,
                TRUE,
                0,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            WHERE NOT EXISTS (
                SELECT 1
                FROM event_types
                WHERE school_id IS NULL
                  AND name = 'Regular Event'
            )
            """
        )

        op.execute(
            """
            UPDATE events
            SET event_type_id = (
                SELECT id
                FROM event_types
                WHERE school_id IS NULL
                  AND name = 'Regular Event'
                LIMIT 1
            )
            WHERE event_type_id IS NULL
            """
        )

        op.drop_column("events", "event_type")

    op.alter_column("event_types", "is_active", server_default=None)
    op.alter_column("event_types", "sort_order", server_default=None)
    op.alter_column("event_types", "created_at", server_default=None)
    op.alter_column("event_types", "updated_at", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    event_columns = (
        {column["name"] for column in inspector.get_columns("events")}
        if "events" in existing_tables
        else set()
    )

    if "event_type" not in event_columns:
        op.add_column(
            "events",
            sa.Column("event_type", sa.String(length=100), nullable=False, server_default="Regular Event"),
        )
        op.execute(
            """
            UPDATE events AS e
            SET event_type = COALESCE(et.name, 'Regular Event')
            FROM event_types AS et
            WHERE e.event_type_id = et.id
            """
        )
        op.alter_column("events", "event_type", server_default=None)

    if "event_type_id" in event_columns:
        op.drop_constraint("fk_events_event_type_id_event_types", "events", type_="foreignkey")
        op.drop_index(op.f("ix_events_event_type_id"), table_name="events")
        op.drop_column("events", "event_type_id")

    op.drop_index(op.f("ix_event_types_school_id"), table_name="event_types")
    op.drop_index(op.f("ix_event_types_id"), table_name="event_types")
    op.drop_table("event_types")

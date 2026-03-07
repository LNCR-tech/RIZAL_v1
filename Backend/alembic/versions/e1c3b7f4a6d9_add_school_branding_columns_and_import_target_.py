"""add_school_branding_columns_and_import_target_school

Revision ID: e1c3b7f4a6d9
Revises: a9d1f5c7b882
Create Date: 2026-03-04 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1c3b7f4a6d9"
down_revision: Union[str, None] = "a9d1f5c7b882"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("schools", sa.Column("school_name", sa.String(length=255), nullable=True))
    op.add_column("schools", sa.Column("school_code", sa.String(length=50), nullable=True))
    op.add_column(
        "schools",
        sa.Column("primary_color", sa.String(length=7), nullable=False, server_default="#162F65"),
    )
    op.add_column("schools", sa.Column("secondary_color", sa.String(length=7), nullable=True))
    op.add_column(
        "schools",
        sa.Column("subscription_status", sa.String(length=30), nullable=False, server_default="trial"),
    )
    op.add_column(
        "schools",
        sa.Column("active_status", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.execute("UPDATE schools SET school_name = name WHERE school_name IS NULL")
    op.execute(
        """
        UPDATE schools s
        SET
            primary_color = COALESCE(ss.primary_color, s.primary_color, '#162F65'),
            secondary_color = COALESCE(ss.secondary_color, s.secondary_color)
        FROM school_settings ss
        WHERE ss.school_id = s.id
        """
    )
    op.alter_column("schools", "school_name", nullable=False)

    op.create_index("ix_schools_school_name", "schools", ["school_name"], unique=False)
    op.create_index("ix_schools_school_code", "schools", ["school_code"], unique=True)

    op.add_column("bulk_import_jobs", sa.Column("target_school_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_bulk_import_jobs_target_school_id_schools",
        "bulk_import_jobs",
        "schools",
        ["target_school_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.execute(
        """
        UPDATE bulk_import_jobs j
        SET target_school_id = u.school_id
        FROM users u
        WHERE j.created_by_user_id = u.id
        """
    )
    op.alter_column("bulk_import_jobs", "target_school_id", nullable=False)
    op.create_index(
        "ix_bulk_import_jobs_target_school_id",
        "bulk_import_jobs",
        ["target_school_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_bulk_import_jobs_target_school_id", table_name="bulk_import_jobs")
    op.drop_constraint(
        "fk_bulk_import_jobs_target_school_id_schools",
        "bulk_import_jobs",
        type_="foreignkey",
    )
    op.drop_column("bulk_import_jobs", "target_school_id")

    op.drop_index("ix_schools_school_code", table_name="schools")
    op.drop_index("ix_schools_school_name", table_name="schools")
    op.drop_column("schools", "active_status")
    op.drop_column("schools", "subscription_status")
    op.drop_column("schools", "secondary_color")
    op.drop_column("schools", "primary_color")
    op.drop_column("schools", "school_code")
    op.drop_column("schools", "school_name")

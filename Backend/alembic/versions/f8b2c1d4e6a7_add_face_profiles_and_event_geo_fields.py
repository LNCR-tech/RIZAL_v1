"""add face profiles and event geo verification fields

Revision ID: f8b2c1d4e6a7
Revises: d4f6a8b0c2e4
Create Date: 2026-03-10 23:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8b2c1d4e6a7"
down_revision: Union[str, None] = "d4f6a8b0c2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_face_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("face_encoding", sa.LargeBinary(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="face_recognition"),
        sa.Column("reference_image_sha256", sa.String(length=64), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.add_column("events", sa.Column("geo_latitude", sa.Float(), nullable=True))
    op.add_column("events", sa.Column("geo_longitude", sa.Float(), nullable=True))
    op.add_column("events", sa.Column("geo_radius_m", sa.Float(), nullable=True))
    op.add_column("events", sa.Column("geo_required", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("events", sa.Column("geo_max_accuracy_m", sa.Float(), nullable=True))

    op.add_column("attendances", sa.Column("geo_distance_m", sa.Float(), nullable=True))
    op.add_column("attendances", sa.Column("geo_effective_distance_m", sa.Float(), nullable=True))
    op.add_column("attendances", sa.Column("geo_latitude", sa.Float(), nullable=True))
    op.add_column("attendances", sa.Column("geo_longitude", sa.Float(), nullable=True))
    op.add_column("attendances", sa.Column("geo_accuracy_m", sa.Float(), nullable=True))
    op.add_column("attendances", sa.Column("liveness_label", sa.String(length=32), nullable=True))
    op.add_column("attendances", sa.Column("liveness_score", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("attendances", "liveness_score")
    op.drop_column("attendances", "liveness_label")
    op.drop_column("attendances", "geo_accuracy_m")
    op.drop_column("attendances", "geo_longitude")
    op.drop_column("attendances", "geo_latitude")
    op.drop_column("attendances", "geo_effective_distance_m")
    op.drop_column("attendances", "geo_distance_m")

    op.drop_column("events", "geo_max_accuracy_m")
    op.drop_column("events", "geo_required")
    op.drop_column("events", "geo_radius_m")
    op.drop_column("events", "geo_longitude")
    op.drop_column("events", "geo_latitude")

    op.drop_table("user_face_profiles")

"""Use: Implements canonical face embedding metadata for student profiles.
Where to use: Use this only when Alembic runs backend database upgrades or downgrades.
Role: Migration layer. It records one step in the database schema history.

add student face embedding metadata

Revision ID: c6e1f4a8b9d0
Revises: b8e4c1d2f7a9
Create Date: 2026-04-03 12:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "c6e1f4a8b9d0"
down_revision: Union[str, None] = "b8e4c1d2f7a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {
        column["name"] for column in inspector.get_columns("student_profiles")
    }

    if "embedding_provider" not in existing_columns:
        op.add_column(
            "student_profiles",
            sa.Column("embedding_provider", sa.String(length=32), nullable=True),
        )
    if "embedding_dtype" not in existing_columns:
        op.add_column(
            "student_profiles",
            sa.Column("embedding_dtype", sa.String(length=16), nullable=True),
        )
    if "embedding_dimension" not in existing_columns:
        op.add_column(
            "student_profiles",
            sa.Column("embedding_dimension", sa.Integer(), nullable=True),
        )
    if "embedding_normalized" not in existing_columns:
        op.add_column(
            "student_profiles",
            sa.Column(
                "embedding_normalized",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        )
        op.alter_column("student_profiles", "embedding_normalized", server_default=None)

    # Legacy face_recognition / dlib embeddings are float64 128-d vectors in the
    # current production system. Mark them explicitly so the new ArcFace runtime
    # can reject mixed-provider comparisons until the student re-enrolls.
    op.execute(
        sa.text(
            """
            UPDATE student_profiles
            SET
                embedding_provider = COALESCE(embedding_provider, 'dlib'),
                embedding_dtype = COALESCE(embedding_dtype, 'float64'),
                embedding_dimension = COALESCE(embedding_dimension, 128),
                embedding_normalized = COALESCE(embedding_normalized, false)
            WHERE face_encoding IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {
        column["name"] for column in inspector.get_columns("student_profiles")
    }

    if "embedding_normalized" in existing_columns:
        op.drop_column("student_profiles", "embedding_normalized")
    if "embedding_dimension" in existing_columns:
        op.drop_column("student_profiles", "embedding_dimension")
    if "embedding_dtype" in existing_columns:
        op.drop_column("student_profiles", "embedding_dtype")
    if "embedding_provider" in existing_columns:
        op.drop_column("student_profiles", "embedding_provider")

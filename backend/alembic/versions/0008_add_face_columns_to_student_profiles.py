"""Add face recognition columns to student_profiles.

Revision ID: 0008_student_face_cols
Revises: 0007_sanction_attend_fk
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_student_face_cols"
down_revision = "0007_sanction_attend_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("student_profiles", sa.Column("face_encoding", sa.LargeBinary(), nullable=True))
    op.add_column("student_profiles", sa.Column("embedding_provider", sa.String(32), nullable=True))
    op.add_column("student_profiles", sa.Column("embedding_dtype", sa.String(16), nullable=True))
    op.add_column("student_profiles", sa.Column("embedding_dimension", sa.Integer(), nullable=True))
    op.add_column("student_profiles", sa.Column("embedding_normalized", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("student_profiles", sa.Column("is_face_registered", sa.Boolean(), nullable=True))
    op.add_column("student_profiles", sa.Column("face_image_url", sa.String(500), nullable=True))
    op.add_column("student_profiles", sa.Column("registration_complete", sa.Boolean(), nullable=True))
    op.add_column("student_profiles", sa.Column("last_face_update", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_student_profiles_is_face_registered", "student_profiles", ["is_face_registered"])
    op.create_index("ix_student_profiles_registration_complete", "student_profiles", ["registration_complete"])


def downgrade() -> None:
    op.drop_index("ix_student_profiles_registration_complete", table_name="student_profiles")
    op.drop_index("ix_student_profiles_is_face_registered", table_name="student_profiles")
    op.drop_column("student_profiles", "last_face_update")
    op.drop_column("student_profiles", "registration_complete")
    op.drop_column("student_profiles", "face_image_url")
    op.drop_column("student_profiles", "is_face_registered")
    op.drop_column("student_profiles", "embedding_normalized")
    op.drop_column("student_profiles", "embedding_dimension")
    op.drop_column("student_profiles", "embedding_dtype")
    op.drop_column("student_profiles", "embedding_provider")
    op.drop_column("student_profiles", "face_encoding")

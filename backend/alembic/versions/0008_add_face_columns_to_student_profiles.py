"""Add the remaining face columns to student_profiles + indexes.

Revision ID: 0008_student_face_cols
Revises: 0007_sanction_attend_fk
Create Date: 2026-05-25

Note: face_encoding, is_face_registered, embedding_provider, embedding_dtype,
embedding_dimension, embedding_normalized are already created by
`bfdc12357b0c_add_face_registration_columns_to_.py` (now an ancestor via the
rebased chain). This migration is the *delta* on top of that — the three
columns that bfdc12357b0c didn't add (face_image_url, registration_complete,
last_face_update) plus the two indexes the runtime queries against.
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_student_face_cols"
down_revision = "0007_sanction_attend_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column("face_image_url", sa.String(500), nullable=True),
    )
    op.add_column(
        "student_profiles",
        sa.Column("registration_complete", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "student_profiles",
        sa.Column("last_face_update", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_student_profiles_is_face_registered",
        "student_profiles",
        ["is_face_registered"],
    )
    op.create_index(
        "ix_student_profiles_registration_complete",
        "student_profiles",
        ["registration_complete"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_student_profiles_registration_complete",
        table_name="student_profiles",
    )
    op.drop_index(
        "ix_student_profiles_is_face_registered",
        table_name="student_profiles",
    )
    op.drop_column("student_profiles", "last_face_update")
    op.drop_column("student_profiles", "registration_complete")
    op.drop_column("student_profiles", "face_image_url")

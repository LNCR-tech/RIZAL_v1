"""add_face_registration_columns_to_student_profiles

Revision ID: bfdc12357b0c
Revises: 0004_school_face_feature_flags
Create Date: 2026-05-09 06:38:15.229019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfdc12357b0c'
down_revision: Union[str, None] = '0004_school_face_feature_flags'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('student_profiles', sa.Column('face_encoding', sa.Text(), nullable=True))
    op.add_column('student_profiles', sa.Column('is_face_registered', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('student_profiles', sa.Column('embedding_provider', sa.Text(), nullable=True))
    op.add_column('student_profiles', sa.Column('embedding_dtype', sa.Text(), nullable=True))
    op.add_column('student_profiles', sa.Column('embedding_dimension', sa.Integer(), nullable=True))
    op.add_column('student_profiles', sa.Column('embedding_normalized', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('student_profiles', 'embedding_normalized')
    op.drop_column('student_profiles', 'embedding_dimension')
    op.drop_column('student_profiles', 'embedding_dtype')
    op.drop_column('student_profiles', 'embedding_provider')
    op.drop_column('student_profiles', 'is_face_registered')
    op.drop_column('student_profiles', 'face_encoding')

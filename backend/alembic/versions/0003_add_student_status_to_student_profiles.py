"""Add student_status and promotion_locked to student_profiles

Revision ID: 0003_add_student_status
Revises: 0002_reports_user_demographics
Create Date: 2026-05-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0003_add_student_status'
down_revision = '0002_reports_user_demographics'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('student_profiles', sa.Column('student_status', sa.Text(), server_default='ACTIVE', nullable=False))
    op.add_column('student_profiles', sa.Column('promotion_locked', sa.Boolean(), server_default=sa.text('false'), nullable=False))

def downgrade() -> None:
    op.drop_column('student_profiles', 'promotion_locked')
    op.drop_column('student_profiles', 'student_status')

"""Add attendance time_in method consistency constraint

Revision ID: add_attendance_consistency_check
Revises: (previous revision)
Create Date: 2024

This migration adds a database constraint to ensure data integrity:
- If time_in is NULL, method must be NULL
- If time_in is NOT NULL, method must NOT be NULL

This prevents invalid attendance records where students have a method
but never actually signed in.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_attendance_consistency_check'
down_revision = '85616f5dcc97'  # Runs after time_in nullable migration
branch_labels = None
depends_on = None


def upgrade():
    """Add check constraint for attendance data consistency."""
    # FIRST: Clean up any existing bad data BEFORE applying constraint
    op.execute("""
        UPDATE attendances 
        SET method = NULL, check_in_status = NULL
        WHERE time_in IS NULL AND method IS NOT NULL
    """)
    
    # SECOND: Add constraint to ensure time_in and method are consistent
    op.create_check_constraint(
        'attendance_time_in_method_consistency',
        'attendances',
        '(time_in IS NULL AND method IS NULL) OR (time_in IS NOT NULL AND method IS NOT NULL)'
    )


def downgrade():
    """Remove the check constraint."""
    op.drop_constraint(
        'attendance_time_in_method_consistency',
        'attendances',  # Fixed: table name is plural
        type_='check'
    )

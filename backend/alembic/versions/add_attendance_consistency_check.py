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
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Add check constraint for attendance data consistency."""
    # Add constraint to ensure time_in and method are consistent
    op.create_check_constraint(
        'attendance_time_in_method_consistency',
        'attendance',
        '(time_in IS NULL AND method IS NULL) OR (time_in IS NOT NULL AND method IS NOT NULL)'
    )
    
    # Optional: Clean up any existing bad data before applying constraint
    # Uncomment if you want to auto-fix bad data during migration
    # op.execute("""
    #     UPDATE attendance 
    #     SET method = NULL, check_in_status = NULL
    #     WHERE time_in IS NULL AND method IS NOT NULL
    # """)


def downgrade():
    """Remove the check constraint."""
    op.drop_constraint(
        'attendance_time_in_method_consistency',
        'attendance',
        type_='check'
    )

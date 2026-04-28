"""Use: Validates attendance data consistency to prevent NULL violations.
Where to use: Import and call before creating/updating attendance records.
Role: Validation layer ensuring data integrity rules are enforced.
"""

from __future__ import annotations

import logging
from datetime import datetime

from app.models.attendance import Attendance as AttendanceModel

logger = logging.getLogger(__name__)


class AttendanceValidationError(ValueError):
    """Raised when attendance data violates consistency rules."""
    pass


def validate_attendance_consistency(
    *,
    time_in: datetime | None,
    time_out: datetime | None,
    method: str | None,
    check_in_status: str | None,
    check_out_status: str | None,
    student_id: int,
    event_id: int,
) -> None:
    """Validate attendance record consistency before database write.
    
    Rules:
    1. If time_in is NULL → method MUST be NULL
    2. If time_in is NOT NULL → method MUST NOT be NULL
    3. If time_in is NULL → check_in_status SHOULD be NULL
    4. If time_out is NULL → check_out_status SHOULD be NULL
    
    Raises:
        AttendanceValidationError: If validation fails
    """
    # Rule 1: NULL time_in requires NULL method
    if time_in is None and method is not None:
        error_msg = (
            f"Attendance validation failed for student_id={student_id}, event_id={event_id}: "
            f"Cannot have method='{method}' when time_in is NULL. "
            f"Students who never signed in must have method=NULL."
        )
        logger.error(error_msg)
        raise AttendanceValidationError(error_msg)
    
    # Rule 2: Non-NULL time_in requires non-NULL method
    if time_in is not None and method is None:
        error_msg = (
            f"Attendance validation failed for student_id={student_id}, event_id={event_id}: "
            f"Cannot have time_in={time_in} without a method. "
            f"All sign-ins must specify how the student signed in."
        )
        logger.error(error_msg)
        raise AttendanceValidationError(error_msg)
    
    # Rule 3: NULL time_in should have NULL check_in_status (warning only)
    if time_in is None and check_in_status is not None:
        logger.warning(
            f"Attendance data inconsistency for student_id={student_id}, event_id={event_id}: "
            f"time_in is NULL but check_in_status='{check_in_status}'. "
            f"Consider setting check_in_status=NULL for students who never signed in."
        )
    
    # Rule 4: NULL time_out should have NULL check_out_status (warning only)
    if time_out is None and check_out_status is not None:
        logger.warning(
            f"Attendance data inconsistency for student_id={student_id}, event_id={event_id}: "
            f"time_out is NULL but check_out_status='{check_out_status}'. "
            f"Consider setting check_out_status=NULL for students who never signed out."
        )
    
    # Log successful validation
    logger.debug(
        f"Attendance validation passed for student_id={student_id}, event_id={event_id}: "
        f"time_in={'SET' if time_in else 'NULL'}, method={method or 'NULL'}"
    )


def validate_attendance_model(attendance: AttendanceModel) -> None:
    """Validate an AttendanceModel instance before commit.
    
    Args:
        attendance: The attendance model to validate
        
    Raises:
        AttendanceValidationError: If validation fails
    """
    validate_attendance_consistency(
        time_in=attendance.time_in,
        time_out=attendance.time_out,
        method=attendance.method,
        check_in_status=attendance.check_in_status,
        check_out_status=attendance.check_out_status,
        student_id=attendance.student_id,
        event_id=attendance.event_id,
    )


def log_attendance_creation(
    *,
    student_id: int,
    event_id: int,
    time_in: datetime | None,
    method: str | None,
    status: str,
    verified_by: int | None = None,
) -> None:
    """Log attendance record creation for audit trail.
    
    Args:
        student_id: Student profile ID
        event_id: Event ID
        time_in: Sign-in timestamp (NULL if never signed in)
        method: Sign-in method (NULL if never signed in)
        status: Attendance status
        verified_by: User ID who verified/created the record
    """
    logger.info(
        f"Creating attendance record: "
        f"student_id={student_id}, event_id={event_id}, "
        f"time_in={'SET' if time_in else 'NULL'}, "
        f"method={method or 'NULL'}, "
        f"status={status}, "
        f"verified_by={verified_by or 'SYSTEM'}"
    )

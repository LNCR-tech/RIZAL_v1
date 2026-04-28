"""Use: Contains the main backend rules for event attendance finalization and support logic.
Where to use: Use this from routers, workers, or other services when event attendance finalization and support logic logic is needed.
Role: Service layer. It keeps business logic out of the route files.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event as EventModel
from app.models.user import StudentProfile, User as UserModel
from app.services.attendance_status import normalize_attendance_status


def get_event_participant_student_ids(db: Session, event: EventModel) -> list[int]:
    """Return the student IDs that fall inside the event's academic scope."""
    query = (
        db.query(StudentProfile.id)
        .join(UserModel, StudentProfile.user_id == UserModel.id)
        .filter(UserModel.school_id == event.school_id)
    )

    program_ids = [program.id for program in event.programs]
    department_ids = [department.id for department in event.departments]

    if program_ids:
        query = query.filter(StudentProfile.program_id.in_(program_ids))
    if department_ids:
        query = query.filter(StudentProfile.department_id.in_(department_ids))

    return [student_id for (student_id,) in query.all()]


def finalize_completed_event_attendance(db: Session, event: EventModel) -> dict[str, int]:
    """Auto-close unfinished attendance and create absent rows once sign-out is fully closed.
    
    This function keeps NULL values for time_in and time_out when students didn't actually
    sign in or sign out. This preserves data integrity and provides accurate audit trails.
    """
    participant_ids = get_event_participant_student_ids(db, event)
    if not participant_ids:
        return {"created_absent": 0, "marked_absent_no_timeout": 0}

    existing_attendances = (
        db.query(AttendanceModel)
        .filter(
            AttendanceModel.event_id == event.id,
            AttendanceModel.student_id.in_(participant_ids),
        )
        .all()
    )

    existing_student_ids = {attendance.student_id for attendance in existing_attendances}

    marked_absent_no_timeout = 0
    for attendance in existing_attendances:
        # Skip if already has sign-out or never signed in
        if attendance.time_in is None or attendance.time_out is not None:
            continue
        if normalize_attendance_status(attendance.status) not in {"present", "late", "absent"}:
            continue
        
        # Keep time_out as NULL - student never signed out
        # Only update status and check_out_status to reflect absence
        attendance.check_out_status = None  # NULL because they didn't sign out
        attendance.status = "absent"
        attendance.notes = "Auto-marked absent - no sign-out recorded."
        marked_absent_no_timeout += 1

    # Create absent records for students who never signed in
    missing_student_ids = [student_id for student_id in participant_ids if student_id not in existing_student_ids]
    for student_id in missing_student_ids:
        db.add(
            AttendanceModel(
                student_id=student_id,
                event_id=event.id,
                time_in=None,  # NULL - never signed in
                time_out=None,  # NULL - never signed out
                method=None,  # NULL - no method because they never signed in
                status="absent",
                check_in_status=None,  # NULL - never signed in
                check_out_status=None,  # NULL - never signed out
                notes="Auto-marked absent - no sign-in recorded.",
            )
        )

    return {
        "created_absent": len(missing_student_ids),
        "marked_absent_no_timeout": marked_absent_no_timeout,
    }

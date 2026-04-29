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
    """Auto-close unfinished attendance for students who signed in but never signed out.

    Only updates rows for students who DID sign in (time_in is not NULL) but have no
    time_out. Does NOT create rows for students who never signed in; absentees are
    computed at report time from participant count minus valid attendance rows.
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

    marked_absent_no_timeout = 0
    for attendance in existing_attendances:
        # Only update rows where student actually signed in but never signed out
        if attendance.time_in is None or attendance.time_out is not None:
            continue
        if normalize_attendance_status(attendance.status) not in {"present", "late", "absent"}:
            continue

        # time_out stays NULL; student signed in but never signed out.
        attendance.check_out_status = None
        attendance.status = "absent"
        attendance.notes = "Auto-marked absent - no sign-out recorded."
        marked_absent_no_timeout += 1

    # Do NOT create rows for students who never signed in.
    # Reports compute absentees as: participant_count - signed_in_count.
    return {
        "created_absent": 0,
        "marked_absent_no_timeout": marked_absent_no_timeout,
    }

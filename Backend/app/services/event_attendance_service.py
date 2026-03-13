from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event as EventModel
from app.models.user import StudentProfile, User as UserModel
from app.services.attendance_status import normalize_attendance_status


def get_event_participant_student_ids(db: Session, event: EventModel) -> list[int]:
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
        if attendance.time_in is None or attendance.time_out is not None:
            continue
        if normalize_attendance_status(attendance.status) not in {"present", "late", "absent"}:
            continue
        attendance.status = "absent"
        attendance.notes = (
            f"Auto-marked absent - no time-out recorded. {attendance.notes or ''}"
        ).strip()
        marked_absent_no_timeout += 1

    missing_student_ids = [student_id for student_id in participant_ids if student_id not in existing_student_ids]
    for student_id in missing_student_ids:
        db.add(
            AttendanceModel(
                student_id=student_id,
                event_id=event.id,
                time_in=event.start_datetime,
                time_out=event.start_datetime,
                method="manual",
                status="absent",
                notes="Auto-marked absent - no sign-in recorded.",
            )
        )

    return {
        "created_absent": len(missing_student_ids),
        "marked_absent_no_timeout": marked_absent_no_timeout,
    }

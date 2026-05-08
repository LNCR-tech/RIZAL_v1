"""Use: Contains the main backend rules for event attendance finalization and support logic.
Where to use: Use this from routers, workers, or other services when event attendance finalization and support logic logic is needed.
Role: Service layer. It keeps business logic out of the route files.
"""

from __future__ import annotations

from datetime import timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event as EventModel, EventTarget, EventTargetScope
from app.models.user import StudentProfile, User as UserModel
from app.schemas.user import StudentStatus
from app.services.attendance_status import (
    finalize_completed_attendance_status,
    normalize_attendance_status,
)
from app.services.event_time_status import (
    get_effective_sign_out_close_time,
    normalize_event_datetime,
)


def get_event_participant_student_ids(db: Session, event: EventModel) -> list[int]:
    """Return the student IDs that fall inside the event's academic scope.
    
    Rules:
    1. Only ACTIVE students are included.
    2. Must match event_targets if present.
    3. Fallback to legacy programs/departments if no targets exist.
    """
    base_query = (
        db.query(StudentProfile.id)
        .join(UserModel, StudentProfile.user_id == UserModel.id)
        .filter(UserModel.school_id == event.school_id)
        .filter(StudentProfile.student_status == StudentStatus.ACTIVE)
    )

    targets = getattr(event, "event_targets", [])
    if not targets:
        # Fallback to legacy logic
        program_ids = [program.id for program in event.programs]
        department_ids = [department.id for department in event.departments]

        if program_ids:
            base_query = base_query.filter(StudentProfile.program_id.in_(program_ids))
        if department_ids:
            base_query = base_query.filter(StudentProfile.department_id.in_(department_ids))
        
        return [student_id for (student_id,) in base_query.all()]

    # Use Phase 4+ targeting logic
    target_filters = []
    for target in targets:
        if target.scope_type == EventTargetScope.ALL:
            # ALL means all ACTIVE students in the school
            return [student_id for (student_id,) in base_query.all()]

        if target.scope_type == EventTargetScope.YEAR_LEVEL:
            target_filters.append(StudentProfile.year_level == target.year_level)
        elif target.scope_type == EventTargetScope.DEPARTMENT:
            target_filters.append(StudentProfile.department_id == target.department_id)
        elif target.scope_type == EventTargetScope.COURSE:
            target_filters.append(StudentProfile.program_id == target.course_id)
        elif target.scope_type == EventTargetScope.DEPARTMENT_YEAR:
            target_filters.append(
                (StudentProfile.department_id == target.department_id) &
                (StudentProfile.year_level == target.year_level)
            )
        elif target.scope_type == EventTargetScope.COURSE_YEAR:
            target_filters.append(
                (StudentProfile.program_id == target.course_id) &
                (StudentProfile.year_level == target.year_level)
            )

    if target_filters:
        base_query = base_query.filter(or_(*target_filters))
    else:
        # If targets exist but none match (should not happen with valid data), return empty
        return []

    return [student_id for (student_id,) in base_query.all()]


def finalize_completed_event_attendance(db: Session, event: EventModel) -> dict[str, int]:
    """Auto-close unfinished attendance and create absent rows once sign-out is fully closed."""
    participant_ids = get_event_participant_student_ids(db, event)
    if not participant_ids:
        return {"created_absent": 0, "marked_absent_no_timeout": 0}

    effective_sign_out_close = get_effective_sign_out_close_time(
        event.end_datetime,
        getattr(event, "sign_out_grace_minutes", 0),
        getattr(event, "sign_out_override_until", None),
    )
    effective_sign_out_close_utc = effective_sign_out_close.astimezone(timezone.utc).replace(tzinfo=None)
    event_start_utc = normalize_event_datetime(event.start_datetime).astimezone(timezone.utc).replace(tzinfo=None)
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
        attendance.time_out = effective_sign_out_close_utc
        attendance.check_out_status = "absent"
        attendance.status, final_note = finalize_completed_attendance_status(
            check_in_status=attendance.check_in_status or attendance.status,
            check_out_status=attendance.check_out_status,
        )
        attendance.notes = (
            f"Auto-marked absent - no sign-out recorded. {final_note or attendance.notes or ''}"
        ).strip()
        marked_absent_no_timeout += 1

    missing_student_ids = [student_id for student_id in participant_ids if student_id not in existing_student_ids]
    for student_id in missing_student_ids:
        db.add(
            AttendanceModel(
                student_id=student_id,
                event_id=event.id,
                time_in=event_start_utc,
                time_out=effective_sign_out_close_utc,
                method="manual",
                status="absent",
                check_in_status=None,
                check_out_status="absent",
                notes="Auto-marked absent - no sign-in recorded.",
            )
        )

    return {
        "created_absent": len(missing_student_ids),
        "marked_absent_no_timeout": marked_absent_no_timeout,
    }

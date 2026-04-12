"""Query helpers for school-level reports."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event
from app.models.user import StudentProfile, User


def build_attendance_summary_query(
    db: Session,
    *,
    school_id: int,
    start_date: date | None,
    end_date: date | None,
    department_id: int | None,
    program_id: int | None,
):
    query = (
        db.query(AttendanceModel)
        .join(Event, AttendanceModel.event_id == Event.id)
        .filter(Event.school_id == school_id)
    )

    if start_date:
        query = query.filter(Event.start_datetime >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Event.start_datetime <= datetime.combine(end_date, datetime.max.time()))

    if department_id or program_id:
        query = (
            query.join(StudentProfile, AttendanceModel.student_id == StudentProfile.id)
            .join(User, StudentProfile.user_id == User.id)
            .filter(User.school_id == school_id)
        )
        if department_id:
            query = query.filter(StudentProfile.department_id == department_id)
        if program_id:
            query = query.filter(StudentProfile.program_id == program_id)

    return query


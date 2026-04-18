"""Query helpers for school-level reports."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event
from app.models.platform_features import LoginHistory
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


def list_student_profiles_for_login_report(
    db: Session,
    *,
    school_id: int,
    department_id: int | None,
    program_id: int | None,
) -> list[StudentProfile]:
    query = (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.user),
            joinedload(StudentProfile.department),
            joinedload(StudentProfile.program),
        )
        .join(User, StudentProfile.user_id == User.id)
        .filter(User.school_id == school_id)
    )

    if department_id:
        query = query.filter(StudentProfile.department_id == department_id)
    if program_id:
        query = query.filter(StudentProfile.program_id == program_id)

    return (
        query.order_by(
            User.last_name.asc(),
            User.first_name.asc(),
            StudentProfile.student_id.asc(),
        )
        .all()
    )


def get_successful_student_login_stats(
    db: Session,
    *,
    school_id: int,
    user_ids: list[int],
    start_date: date | None,
    end_date: date | None,
) -> dict[int, dict[str, object]]:
    if not user_ids:
        return {}

    query = (
        db.query(
            LoginHistory.user_id.label("user_id"),
            func.count(LoginHistory.id).label("successful_login_count"),
            func.max(LoginHistory.created_at).label("last_login_at"),
        )
        .filter(
            LoginHistory.school_id == school_id,
            LoginHistory.user_id.in_(user_ids),
            LoginHistory.success.is_(True),
        )
    )

    if start_date:
        query = query.filter(LoginHistory.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(LoginHistory.created_at <= datetime.combine(end_date, datetime.max.time()))

    rows = query.group_by(LoginHistory.user_id).all()
    return {
        int(row.user_id): {
            "successful_login_count": int(row.successful_login_count or 0),
            "last_login_at": row.last_login_at,
        }
        for row in rows
        if row.user_id is not None
    }

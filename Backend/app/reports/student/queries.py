"""Query helpers for student-focused reports."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import String, func, literal, or_
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event
from app.models.user import StudentProfile, User
from app.routers.attendance.shared import _apply_student_scope_filters


def _event_type_column():
    """Return the event type ORM column when available in this schema version."""
    return getattr(Event, "event_type", None)


def build_students_overview_base_query(
    db: Session,
    *,
    school_id: int,
    governance_units,
    department_id: Optional[int],
    program_id: Optional[int],
    search: Optional[str],
):
    query = (
        db.query(StudentProfile)
        .join(User, StudentProfile.user_id == User.id)
        .filter(User.school_id == school_id)
    )
    query = _apply_student_scope_filters(query, governance_units)

    if department_id:
        query = query.filter(StudentProfile.department_id == department_id)
    if program_id:
        query = query.filter(StudentProfile.program_id == program_id)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                StudentProfile.student_id.ilike(search_filter),
                func.concat(
                    User.first_name,
                    " ",
                    func.coalesce(User.middle_name + " ", ""),
                    User.last_name,
                ).ilike(search_filter),
            )
        )
    return query


def count_students(query) -> int:
    return int(query.count() or 0)


def list_students_overview_page(query, *, skip: int, limit: int) -> list[StudentProfile]:
    return (
        query.options(
            joinedload(StudentProfile.user),
            joinedload(StudentProfile.department),
            joinedload(StudentProfile.program),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_attendances_for_students_overview(
    db: Session,
    *,
    student_ids: list[int],
    school_id: int,
    governance_units,
    allowed_event_ids: list[int],
    start_date: date | None,
    end_date: date | None,
) -> list[AttendanceModel]:
    if not student_ids:
        return []

    attendance_query = (
        db.query(AttendanceModel)
        .join(Event, AttendanceModel.event_id == Event.id)
        .filter(
            AttendanceModel.student_id.in_(student_ids),
            Event.school_id == school_id,
        )
    )

    if governance_units:
        if not allowed_event_ids:
            return []
        attendance_query = attendance_query.filter(Event.id.in_(allowed_event_ids))

    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        attendance_query = attendance_query.filter(Event.start_datetime >= start_datetime)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        attendance_query = attendance_query.filter(Event.start_datetime <= end_datetime)

    return attendance_query.order_by(
        AttendanceModel.student_id.asc(),
        AttendanceModel.event_id.asc(),
        AttendanceModel.time_in.desc(),
        AttendanceModel.id.desc(),
    ).all()


def get_student_profile_for_report(
    db: Session,
    *,
    school_id: int,
    student_profile_id: int,
) -> StudentProfile | None:
    return (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.user),
            joinedload(StudentProfile.department),
            joinedload(StudentProfile.program),
        )
        .join(User, StudentProfile.user_id == User.id)
        .filter(
            StudentProfile.id == student_profile_id,
            User.school_id == school_id,
        )
        .first()
    )


def list_student_attendances_for_report(
    db: Session,
    *,
    school_id: int,
    student_profile_id: int,
    governance_units,
    allowed_event_ids: list[int],
    start_date: date | None,
    end_date: date | None,
    event_type: str | None,
) -> list[AttendanceModel]:
    attendance_query = (
        db.query(AttendanceModel)
        .options(joinedload(AttendanceModel.event))
        .join(Event, AttendanceModel.event_id == Event.id)
        .filter(
            AttendanceModel.student_id == student_profile_id,
            Event.school_id == school_id,
        )
    )
    if governance_units:
        if not allowed_event_ids:
            return []
        attendance_query = attendance_query.filter(Event.id.in_(allowed_event_ids))

    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        attendance_query = attendance_query.filter(Event.start_datetime >= start_datetime)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        attendance_query = attendance_query.filter(Event.start_datetime <= end_datetime)
    event_type_column = _event_type_column()
    if event_type and event_type_column is not None:
        attendance_query = attendance_query.filter(event_type_column == event_type)

    return attendance_query.order_by(Event.start_datetime.desc()).all()


def student_exists_in_school(
    db: Session,
    *,
    school_id: int,
    student_profile_id: int,
) -> bool:
    row = (
        db.query(StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .filter(
            StudentProfile.id == student_profile_id,
            User.school_id == school_id,
        )
        .first()
    )
    return row is not None


def build_student_stats_base_query(
    db: Session,
    *,
    school_id: int,
    student_profile_id: int,
    start_date: date | None,
    end_date: date | None,
):
    query = (
        db.query(AttendanceModel)
        .join(Event, AttendanceModel.event_id == Event.id)
        .filter(
            AttendanceModel.student_id == student_profile_id,
            Event.school_id == school_id,
        )
    )
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(Event.start_datetime >= start_datetime)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(Event.start_datetime <= end_datetime)
    return query


def list_student_status_counts(base_query) -> list[tuple[str | None, int]]:
    rows = (
        base_query.with_entities(
            AttendanceModel.status,
            func.count(AttendanceModel.id).label("count"),
        )
        .group_by(AttendanceModel.status)
        .all()
    )
    return [(status, int(count or 0)) for status, count in rows]


def list_student_trend_results(base_query, *, trunc_period: str):
    return (
        base_query.with_entities(
            func.date_trunc(trunc_period, Event.start_datetime).label("period"),
            AttendanceModel.status,
            func.count(AttendanceModel.id).label("count"),
        )
        .filter(Event.start_datetime.isnot(None))
        .group_by(
            func.date_trunc(trunc_period, Event.start_datetime),
            AttendanceModel.status,
        )
        .order_by("period")
        .all()
    )


def list_student_event_type_breakdown(base_query):
    event_type_column = _event_type_column()
    if event_type_column is None:
        return (
            base_query.with_entities(
                literal("Regular Events", type_=String).label("type"),
                AttendanceModel.status,
                func.count(AttendanceModel.id).label("count"),
            )
            .group_by(AttendanceModel.status)
            .all()
        )

    return (
        base_query.with_entities(
            event_type_column.label("type"),
            AttendanceModel.status,
            func.count(AttendanceModel.id).label("count"),
        )
        .group_by(event_type_column, AttendanceModel.status)
        .all()
    )


def list_all_student_record_rows(
    db: Session,
    *,
    school_id: int,
    student_ids: list[str] | None,
    event_id: int | None,
    skip: int,
    limit: int,
):
    query = (
        db.query(
            AttendanceModel,
            StudentProfile.student_id,
            User.first_name,
            User.last_name,
            Event.name.label("event_name"),
        )
        .join(StudentProfile, AttendanceModel.student_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .join(Event, AttendanceModel.event_id == Event.id)
        .filter(
            User.school_id == school_id,
            Event.school_id == school_id,
        )
    )
    if student_ids:
        query = query.filter(StudentProfile.student_id.in_(student_ids))
    if event_id:
        query = query.filter(AttendanceModel.event_id == event_id)

    return (
        query.order_by(
            StudentProfile.student_id,
            AttendanceModel.time_in.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_student_profile_by_student_code(
    db: Session,
    *,
    school_id: int,
    student_id: str,
) -> StudentProfile | None:
    return (
        db.query(StudentProfile)
        .join(User, StudentProfile.user_id == User.id)
        .filter(
            StudentProfile.student_id == student_id,
            User.school_id == school_id,
        )
        .first()
    )


def list_student_record_rows(
    db: Session,
    *,
    school_id: int,
    student_profile_id: int,
    event_id: int | None,
    skip: int,
    limit: int,
):
    query = (
        db.query(
            AttendanceModel,
            Event.name.label("event_name"),
        )
        .join(Event, AttendanceModel.event_id == Event.id)
        .filter(
            AttendanceModel.student_id == student_profile_id,
            Event.school_id == school_id,
        )
    )
    if event_id:
        query = query.filter(AttendanceModel.event_id == event_id)

    return (
        query.order_by(AttendanceModel.time_in.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

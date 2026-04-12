"""Query helpers for attendance event-level reports."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event
from app.models.program import Program
from app.models.user import StudentProfile, User


def get_event_for_report(
    db: Session,
    *,
    event_id: int,
    actor_school_id: int | None,
) -> Event | None:
    query = (
        db.query(Event)
        .options(
            joinedload(Event.programs),
            joinedload(Event.departments),
        )
        .filter(Event.id == event_id)
    )
    if actor_school_id is not None:
        query = query.filter(Event.school_id == actor_school_id)
    return query.first()


def build_participant_subquery(
    db: Session,
    *,
    school_id: int,
    program_ids: list[int],
    department_ids: list[int],
) -> Any:
    participant_query = (
        db.query(
            StudentProfile.id.label("student_id"),
            StudentProfile.program_id.label("program_id"),
        )
        .join(User, StudentProfile.user_id == User.id)
        .filter(User.school_id == school_id)
    )
    if program_ids:
        participant_query = participant_query.filter(StudentProfile.program_id.in_(program_ids))
    if department_ids:
        participant_query = participant_query.filter(StudentProfile.department_id.in_(department_ids))
    return participant_query.subquery()


def count_participants_from_subquery(db: Session, participant_subquery: Any) -> int:
    return int(db.query(func.count()).select_from(participant_subquery).scalar() or 0)


def count_participants_by_program_from_subquery(
    db: Session,
    participant_subquery: Any,
) -> dict[int | None, int]:
    rows = (
        db.query(
            participant_subquery.c.program_id,
            func.count().label("total"),
        )
        .group_by(participant_subquery.c.program_id)
        .all()
    )
    return {program_id: int(total or 0) for program_id, total in rows}


def list_event_attendance_rows_for_report(
    db: Session,
    *,
    event_id: int,
    participant_subquery: Any,
) -> list[tuple[AttendanceModel, int | None]]:
    return (
        db.query(
            AttendanceModel,
            participant_subquery.c.program_id,
        )
        .join(
            participant_subquery,
            AttendanceModel.student_id == participant_subquery.c.student_id,
        )
        .filter(AttendanceModel.event_id == event_id)
        .order_by(
            AttendanceModel.student_id.asc(),
            AttendanceModel.time_in.desc(),
            AttendanceModel.id.desc(),
        )
        .all()
    )


def list_program_models(
    db: Session,
    *,
    school_id: int,
    program_ids: set[int],
) -> list[Program]:
    if not program_ids:
        return []
    return (
        db.query(Program)
        .filter(
            Program.school_id == school_id,
            Program.id.in_(program_ids),
        )
        .order_by(Program.name.asc())
        .all()
    )


def list_event_attendance_rows_for_attendees(
    db: Session,
    *,
    event_id: int,
) -> list[AttendanceModel]:
    return (
        db.query(AttendanceModel)
        .filter(AttendanceModel.event_id == event_id)
        .order_by(AttendanceModel.status, AttendanceModel.time_in)
        .all()
    )


def list_event_attendance_rows_for_status(
    db: Session,
    *,
    event_id: int,
    school_id: int,
) -> list[AttendanceModel]:
    return (
        db.query(AttendanceModel)
        .join(Event, AttendanceModel.event_id == Event.id)
        .filter(
            AttendanceModel.event_id == event_id,
            Event.school_id == school_id,
        )
        .order_by(AttendanceModel.time_in.desc())
        .all()
    )


def list_event_attendance_with_students(
    db: Session,
    *,
    event_id: int,
    school_id: int,
    active_only: bool | None = None,
    skip: int | None = None,
    limit: int | None = None,
) -> list[tuple[AttendanceModel, str, str, str]]:
    query = (
        db.query(
            AttendanceModel,
            StudentProfile.student_id,
            User.first_name,
            User.last_name,
        )
        .join(StudentProfile, AttendanceModel.student_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .join(Event, AttendanceModel.event_id == Event.id)
        .filter(
            AttendanceModel.event_id == event_id,
            Event.school_id == school_id,
            User.school_id == school_id,
        )
    )
    if active_only is True:
        query = query.filter(AttendanceModel.time_out.is_(None))

    query = query.order_by(AttendanceModel.time_in.desc())
    if skip is not None:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


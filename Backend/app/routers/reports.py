"""Dedicated reporting routes for recommended cross-domain reports."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_db
from app.core.security import get_current_user, get_school_id_or_403, has_any_role
from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event, EventStatus
from app.models.governance_hierarchy import GovernanceUnitType
from app.models.user import StudentProfile, User
from app.routers.attendance.shared import (
    _apply_student_scope_filters,
    _attendance_display_status_value,
    _attendance_is_valid_value,
    _ensure_attendance_report_access,
    _get_attendance_governance_units,
    _get_event_ids_in_attendance_scope,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _validate_date_range(
    start_date: date | None,
    end_date: date | None,
) -> tuple[datetime | None, datetime | None]:
    start_datetime = datetime.combine(start_date, time.min) if start_date else None
    end_datetime = datetime.combine(end_date, time.max) if end_date else None
    if start_datetime and end_datetime and start_datetime > end_datetime:
        raise HTTPException(status_code=400, detail="start_date must be on or before end_date")
    return start_datetime, end_datetime


def _event_status_value(event: Event) -> str:
    if isinstance(event.status, EventStatus):
        return event.status.value
    return str(event.status or "").lower()


def _resolve_scope(
    db: Session,
    *,
    current_user: User,
    governance_context: GovernanceUnitType | None,
    allow_student_view: bool = False,
) -> tuple[int, list[Any], bool]:
    try:
        _ensure_attendance_report_access(db, current_user)
        school_id = get_school_id_or_403(current_user)
        governance_units = _get_attendance_governance_units(
            db,
            current_user=current_user,
            governance_context=governance_context,
        )
        return school_id, governance_units, False
    except HTTPException as exc:
        if allow_student_view and exc.status_code == 403 and has_any_role(current_user, ["student"]):
            school_id = get_school_id_or_403(current_user)
            return school_id, [], True
        raise


def _event_matches_optional_scope(
    event: Event,
    *,
    department_id: int | None,
    program_id: int | None,
) -> bool:
    if department_id is not None:
        event_department_ids = {department.id for department in event.departments}
        if department_id not in event_department_ids:
            return False
    if program_id is not None:
        event_program_ids = {program.id for program in event.programs}
        if program_id not in event_program_ids:
            return False
    return True


def _resolve_time_block(timestamp: datetime | None) -> str:
    if timestamp is None:
        return "unknown"
    hour = timestamp.hour
    if 5 <= hour < 8:
        return "early_morning"
    if 8 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def _student_full_name(student: StudentProfile) -> str:
    first_name = getattr(student.user, "first_name", "") or ""
    middle_name = getattr(student.user, "middle_name", "") or ""
    last_name = getattr(student.user, "last_name", "") or ""
    middle_part = f"{middle_name} " if middle_name else ""
    return f"{first_name} {middle_part}{last_name}".strip() or f"Student #{student.id}"


def _student_payload(student: StudentProfile) -> dict[str, Any]:
    return {
        "id": student.id,
        "student_id": student.student_id,
        "full_name": _student_full_name(student),
        "department_id": student.department_id,
        "program_id": student.program_id,
        "year_level": student.year_level,
        "department_name": getattr(student.department, "name", None) if student.department else None,
        "program_name": getattr(student.program, "name", None) if student.program else None,
    }


def _load_scoped_students(
    db: Session,
    *,
    school_id: int,
    governance_units,
    department_id: int | None,
    program_id: int | None,
) -> list[StudentProfile]:
    query = (
        db.query(StudentProfile)
        .join(User, StudentProfile.user_id == User.id)
        .options(
            joinedload(StudentProfile.user),
            joinedload(StudentProfile.department),
            joinedload(StudentProfile.program),
        )
        .filter(User.school_id == school_id)
    )
    query = _apply_student_scope_filters(query, governance_units)
    if department_id is not None:
        query = query.filter(StudentProfile.department_id == department_id)
    if program_id is not None:
        query = query.filter(StudentProfile.program_id == program_id)
    return query.all()


def _load_scoped_events(
    db: Session,
    *,
    school_id: int,
    governance_units,
    start_datetime: datetime | None,
    end_datetime: datetime | None,
    department_id: int | None,
    program_id: int | None,
    event_id: int | None = None,
) -> list[Event]:
    query = (
        db.query(Event)
        .options(
            joinedload(Event.departments),
            joinedload(Event.programs),
        )
        .filter(Event.school_id == school_id)
    )
    if event_id is not None:
        query = query.filter(Event.id == event_id)
    if start_datetime is not None:
        query = query.filter(Event.start_datetime >= start_datetime)
    if end_datetime is not None:
        query = query.filter(Event.start_datetime <= end_datetime)

    if governance_units:
        allowed_event_ids = _get_event_ids_in_attendance_scope(
            db,
            school_id=school_id,
            governance_units=governance_units,
        )
        if not allowed_event_ids:
            return []
        query = query.filter(Event.id.in_(allowed_event_ids))

    events = query.order_by(Event.start_datetime.asc(), Event.id.asc()).all()
    return [
        event
        for event in events
        if _event_matches_optional_scope(
            event,
            department_id=department_id,
            program_id=program_id,
        )
    ]


def _load_latest_attendance_records(
    db: Session,
    *,
    school_id: int,
    student_ids: list[int],
    event_ids: list[int],
) -> list[AttendanceModel]:
    if not student_ids or not event_ids:
        return []

    rows = (
        db.query(AttendanceModel)
        .join(Event, AttendanceModel.event_id == Event.id)
        .filter(
            Event.school_id == school_id,
            AttendanceModel.student_id.in_(student_ids),
            AttendanceModel.event_id.in_(event_ids),
        )
        .order_by(
            AttendanceModel.student_id.asc(),
            AttendanceModel.event_id.asc(),
            AttendanceModel.time_in.desc(),
            AttendanceModel.id.desc(),
        )
        .all()
    )

    latest_by_student_event: dict[tuple[int, int], AttendanceModel] = {}
    for attendance in rows:
        latest_by_student_event.setdefault((attendance.student_id, attendance.event_id), attendance)
    return list(latest_by_student_event.values())


def _group_student_metrics(
    students: list[StudentProfile],
    attendance_rows: list[AttendanceModel],
) -> list[dict[str, Any]]:
    attendance_by_student: dict[int, list[AttendanceModel]] = defaultdict(list)
    for attendance in attendance_rows:
        attendance_by_student[attendance.student_id].append(attendance)

    metrics: list[dict[str, Any]] = []
    for student in students:
        student_rows = attendance_by_student.get(student.id, [])
        total_events = len(student_rows)
        attended_count = sum(1 for row in student_rows if _attendance_is_valid_value(row))
        late_count = sum(1 for row in student_rows if _attendance_display_status_value(row) == "late")
        absent_count = sum(1 for row in student_rows if _attendance_display_status_value(row) == "absent")
        excused_count = sum(1 for row in student_rows if _attendance_display_status_value(row) == "excused")
        incomplete_count = sum(1 for row in student_rows if _attendance_display_status_value(row) == "incomplete")
        attendance_rate = round((attended_count / total_events) * 100, 2) if total_events > 0 else 0.0

        metrics.append(
            {
                **_student_payload(student),
                "total_events": total_events,
                "attended_count": attended_count,
                "late_count": late_count,
                "absent_count": absent_count,
                "excused_count": excused_count,
                "incomplete_count": incomplete_count,
                "attendance_rate": attendance_rate,
            }
        )
    return metrics


def _build_event_participation_summary(
    event: Event,
    students: list[StudentProfile],
    latest_attendance_map: dict[tuple[int, int], AttendanceModel],
) -> dict[str, Any]:
    event_program_ids = {program.id for program in event.programs}
    event_department_ids = {department.id for department in event.departments}

    participant_ids: list[int] = []
    for student in students:
        if event_program_ids and student.program_id not in event_program_ids:
            continue
        if event_department_ids and student.department_id not in event_department_ids:
            continue
        participant_ids.append(student.id)

    valid_attended = 0
    late_count = 0
    absent_count = 0
    excused_count = 0
    incomplete_count = 0

    for student_id in participant_ids:
        attendance = latest_attendance_map.get((student_id, event.id))
        if attendance is None:
            absent_count += 1
            continue

        display_status = _attendance_display_status_value(attendance)
        if _attendance_is_valid_value(attendance):
            valid_attended += 1
            if display_status == "late":
                late_count += 1
            continue

        if display_status == "incomplete":
            incomplete_count += 1
        elif display_status == "excused":
            excused_count += 1
        else:
            absent_count += 1

    total_participants = len(participant_ids)
    no_show_rate = round((absent_count / total_participants) * 100, 2) if total_participants > 0 else 0.0
    incomplete_rate = round((incomplete_count / total_participants) * 100, 2) if total_participants > 0 else 0.0
    late_rate = round((late_count / total_participants) * 100, 2) if total_participants > 0 else 0.0
    attendance_rate = round((valid_attended / total_participants) * 100, 2) if total_participants > 0 else 0.0

    return {
        "event_id": event.id,
        "event_name": event.name,
        "event_date": event.start_datetime.isoformat() if event.start_datetime else None,
        "event_status": _event_status_value(event),
        "total_participants": total_participants,
        "attended_count": valid_attended,
        "late_count": late_count,
        "incomplete_count": incomplete_count,
        "absent_count": absent_count,
        "excused_count": excused_count,
        "attendance_rate": attendance_rate,
        "no_show_rate": no_show_rate,
        "incomplete_rate": incomplete_rate,
        "late_rate": late_rate,
    }


@router.get("/attendance/at-risk")
def get_at_risk_attendance_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    threshold: float = Query(default=75.0, ge=0, le=100),
    min_events: int = Query(default=3, ge=1),
    limit: int = Query(default=100, ge=1, le=500),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
    )
    attendance_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=[student.id for student in students],
        event_ids=[event.id for event in events],
    )

    rows = [
        row
        for row in _group_student_metrics(students, attendance_rows)
        if row["total_events"] >= min_events and row["attendance_rate"] < threshold
    ]
    rows.sort(key=lambda row: (row["attendance_rate"], -row["total_events"], row["full_name"].lower()))

    return {
        "threshold": threshold,
        "min_events": min_events,
        "total_matches": len(rows),
        "rows": rows[:limit],
    }


@router.get("/attendance/top-absentees")
def get_top_absentees_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
    )
    attendance_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=[student.id for student in students],
        event_ids=[event.id for event in events],
    )

    rows = [row for row in _group_student_metrics(students, attendance_rows) if row["absent_count"] > 0]
    rows.sort(key=lambda row: (-row["absent_count"], row["attendance_rate"], row["full_name"].lower()))

    return {
        "total_matches": len(rows),
        "rows": rows[:limit],
    }


@router.get("/attendance/top-late")
def get_top_late_students_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    metric: str = Query(default="count", pattern="^(count|rate)$"),
    min_events: int = Query(default=3, ge=1),
    limit: int = Query(default=50, ge=1, le=500),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
    )
    attendance_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=[student.id for student in students],
        event_ids=[event.id for event in events],
    )

    rows = []
    for row in _group_student_metrics(students, attendance_rows):
        total_events = row["total_events"]
        late_count = row["late_count"]
        late_rate = round((late_count / total_events) * 100, 2) if total_events > 0 else 0.0
        if total_events < min_events or late_count <= 0:
            continue
        rows.append({**row, "late_rate": late_rate})

    if metric == "rate":
        rows.sort(key=lambda row: (-row["late_rate"], -row["late_count"], row["full_name"].lower()))
    else:
        rows.sort(key=lambda row: (-row["late_count"], -row["late_rate"], row["full_name"].lower()))

    return {
        "metric": metric,
        "min_events": min_events,
        "total_matches": len(rows),
        "rows": rows[:limit],
    }


@router.get("/attendance/leaderboard")
def get_attendance_leaderboard_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    min_events: int = Query(default=3, ge=1),
    limit: int = Query(default=100, ge=1, le=500),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, student_view = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
        allow_student_view=True,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
    )
    attendance_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=[student.id for student in students],
        event_ids=[event.id for event in events],
    )

    leaderboard_rows = [
        row
        for row in _group_student_metrics(students, attendance_rows)
        if row["total_events"] >= min_events
    ]
    leaderboard_rows.sort(
        key=lambda row: (-row["attendance_rate"], -row["attended_count"], row["late_count"], row["full_name"].lower())
    )

    rows = []
    viewer_row = None
    viewer_rank = None
    viewer_student_profile_id = current_user.student_profile.id if current_user.student_profile else None
    for index, row in enumerate(leaderboard_rows, start=1):
        ranked_row = {**row, "rank": index}
        rows.append(ranked_row)
        if viewer_student_profile_id is not None and row["id"] == viewer_student_profile_id:
            viewer_rank = index
            viewer_row = ranked_row

    return {
        "is_student_view": student_view,
        "min_events": min_events,
        "total_ranked_students": len(rows),
        "viewer_rank": viewer_rank,
        "viewer_row": viewer_row,
        "rows": rows[:limit],
    }


def _build_period_rate_map(
    students: list[StudentProfile],
    attendance_rows: list[AttendanceModel],
) -> dict[int, dict[str, Any]]:
    return {
        row["id"]: row
        for row in _group_student_metrics(students, attendance_rows)
    }


@router.get("/attendance/recovery")
def get_attendance_recovery_report(
    current_start_date: date = Query(...),
    current_end_date: date = Query(...),
    previous_start_date: date = Query(...),
    previous_end_date: date = Query(...),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    min_events_per_period: int = Query(default=2, ge=1),
    limit: int = Query(default=100, ge=1, le=500),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    current_start_dt, current_end_dt = _validate_date_range(current_start_date, current_end_date)
    previous_start_dt, previous_end_dt = _validate_date_range(previous_start_date, previous_end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    student_ids = [student.id for student in students]

    current_events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=current_start_dt,
        end_datetime=current_end_dt,
        department_id=department_id,
        program_id=program_id,
    )
    previous_events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=previous_start_dt,
        end_datetime=previous_end_dt,
        department_id=department_id,
        program_id=program_id,
    )

    current_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=student_ids,
        event_ids=[event.id for event in current_events],
    )
    previous_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=student_ids,
        event_ids=[event.id for event in previous_events],
    )

    current_rate_map = _build_period_rate_map(students, current_rows)
    previous_rate_map = _build_period_rate_map(students, previous_rows)

    rows = []
    for student in students:
        current_metric = current_rate_map.get(student.id, {})
        previous_metric = previous_rate_map.get(student.id, {})
        current_total_events = int(current_metric.get("total_events", 0))
        previous_total_events = int(previous_metric.get("total_events", 0))
        if current_total_events < min_events_per_period or previous_total_events < min_events_per_period:
            continue

        current_rate = float(current_metric.get("attendance_rate", 0.0))
        previous_rate = float(previous_metric.get("attendance_rate", 0.0))
        rate_change = round(current_rate - previous_rate, 2)
        if rate_change <= 0:
            continue

        rows.append(
            {
                **_student_payload(student),
                "current_rate": current_rate,
                "previous_rate": previous_rate,
                "rate_change": rate_change,
                "current_total_events": current_total_events,
                "previous_total_events": previous_total_events,
            }
        )

    rows.sort(key=lambda row: (-row["rate_change"], -row["current_rate"], row["full_name"].lower()))
    return {
        "min_events_per_period": min_events_per_period,
        "total_matches": len(rows),
        "rows": rows[:limit],
    }


@router.get("/attendance/decline-alerts")
def get_attendance_decline_report(
    current_start_date: date = Query(...),
    current_end_date: date = Query(...),
    previous_start_date: date = Query(...),
    previous_end_date: date = Query(...),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    decline_threshold: float = Query(default=10.0, ge=0, le=100),
    min_events_per_period: int = Query(default=2, ge=1),
    limit: int = Query(default=100, ge=1, le=500),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    current_start_dt, current_end_dt = _validate_date_range(current_start_date, current_end_date)
    previous_start_dt, previous_end_dt = _validate_date_range(previous_start_date, previous_end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    student_ids = [student.id for student in students]

    current_events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=current_start_dt,
        end_datetime=current_end_dt,
        department_id=department_id,
        program_id=program_id,
    )
    previous_events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=previous_start_dt,
        end_datetime=previous_end_dt,
        department_id=department_id,
        program_id=program_id,
    )

    current_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=student_ids,
        event_ids=[event.id for event in current_events],
    )
    previous_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=student_ids,
        event_ids=[event.id for event in previous_events],
    )

    current_rate_map = _build_period_rate_map(students, current_rows)
    previous_rate_map = _build_period_rate_map(students, previous_rows)

    rows = []
    for student in students:
        current_metric = current_rate_map.get(student.id, {})
        previous_metric = previous_rate_map.get(student.id, {})
        current_total_events = int(current_metric.get("total_events", 0))
        previous_total_events = int(previous_metric.get("total_events", 0))
        if current_total_events < min_events_per_period or previous_total_events < min_events_per_period:
            continue

        current_rate = float(current_metric.get("attendance_rate", 0.0))
        previous_rate = float(previous_metric.get("attendance_rate", 0.0))
        rate_change = round(current_rate - previous_rate, 2)
        if rate_change > -abs(decline_threshold):
            continue

        rows.append(
            {
                **_student_payload(student),
                "current_rate": current_rate,
                "previous_rate": previous_rate,
                "rate_change": rate_change,
                "current_total_events": current_total_events,
                "previous_total_events": previous_total_events,
            }
        )

    rows.sort(key=lambda row: (row["rate_change"], row["current_rate"], row["full_name"].lower()))
    return {
        "decline_threshold": decline_threshold,
        "min_events_per_period": min_events_per_period,
        "total_matches": len(rows),
        "rows": rows[:limit],
    }


def _load_event_participation_dataset(
    db: Session,
    *,
    school_id: int,
    governance_units,
    start_datetime: datetime | None,
    end_datetime: datetime | None,
    department_id: int | None,
    program_id: int | None,
    event_id: int | None,
) -> tuple[list[StudentProfile], list[Event], dict[tuple[int, int], AttendanceModel]]:
    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
        event_id=event_id,
    )
    attendance_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=[student.id for student in students],
        event_ids=[event.id for event in events],
    )
    latest_map = {(attendance.student_id, attendance.event_id): attendance for attendance in attendance_rows}
    return students, events, latest_map


@router.get("/events/no-show")
def get_no_show_event_report(
    event_id: int | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students, events, latest_map = _load_event_participation_dataset(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
        event_id=event_id,
    )
    if event_id is not None and not events:
        raise HTTPException(status_code=404, detail="Event not found")

    rows = [
        _build_event_participation_summary(event, students, latest_map)
        for event in events
    ]
    rows.sort(key=lambda row: (-row["no_show_rate"], -row["absent_count"], row["event_name"].lower()))
    return {"rows": rows}


@router.get("/events/execution-quality")
def get_event_execution_quality_report(
    event_id: int | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students, events, latest_map = _load_event_participation_dataset(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
        event_id=event_id,
    )
    if event_id is not None and not events:
        raise HTTPException(status_code=404, detail="Event not found")

    rows = []
    for event in events:
        summary = _build_event_participation_summary(event, students, latest_map)
        rows.append(
            {
                **summary,
                "execution_quality_score": round(
                    max(0.0, 100.0 - summary["incomplete_rate"] - summary["late_rate"]),
                    2,
                ),
            }
        )
    rows.sort(
        key=lambda row: (
            row["execution_quality_score"],
            -row["incomplete_rate"],
            -row["late_rate"],
            row["event_name"].lower(),
        )
    )
    return {"rows": rows}


@router.get("/events/completion-vs-cancellation")
def get_event_completion_vs_cancellation_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
    )

    completed_count = 0
    cancelled_count = 0
    for event in events:
        status_value = _event_status_value(event)
        if status_value == EventStatus.COMPLETED.value:
            completed_count += 1
        elif status_value == EventStatus.CANCELLED.value:
            cancelled_count += 1

    terminal_total = completed_count + cancelled_count
    completion_rate = round((completed_count / terminal_total) * 100, 2) if terminal_total > 0 else 0.0
    cancellation_rate = round((cancelled_count / terminal_total) * 100, 2) if terminal_total > 0 else 0.0

    rows = [
        {
            "event_id": event.id,
            "event_name": event.name,
            "event_date": event.start_datetime.isoformat() if event.start_datetime else None,
            "event_status": _event_status_value(event),
        }
        for event in events
    ]

    return {
        "summary": {
            "completed_count": completed_count,
            "cancelled_count": cancelled_count,
            "terminal_total": terminal_total,
            "completion_rate": completion_rate,
            "cancellation_rate": cancellation_rate,
        },
        "rows": rows,
    }


@router.get("/attendance/by-day-of-week")
def get_attendance_by_day_of_week_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
    )
    event_by_id = {event.id: event for event in events}
    attendance_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=[student.id for student in students],
        event_ids=list(event_by_id.keys()),
    )

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grouped: dict[str, dict[str, Any]] = {
        day: {
            "day_of_week": day,
            "total_records": 0,
            "attended_count": 0,
            "late_count": 0,
            "incomplete_count": 0,
            "absent_count": 0,
            "excused_count": 0,
        }
        for day in day_order
    }

    for attendance in attendance_rows:
        event = event_by_id.get(attendance.event_id)
        if event is None or event.start_datetime is None:
            continue

        day_name = event.start_datetime.strftime("%A")
        bucket = grouped.get(day_name)
        if bucket is None:
            continue

        bucket["total_records"] += 1
        if _attendance_is_valid_value(attendance):
            bucket["attended_count"] += 1

        display_status = _attendance_display_status_value(attendance)
        if display_status == "late":
            bucket["late_count"] += 1
        elif display_status == "incomplete":
            bucket["incomplete_count"] += 1
        elif display_status == "absent":
            bucket["absent_count"] += 1
        elif display_status == "excused":
            bucket["excused_count"] += 1

    rows = []
    for day in day_order:
        bucket = grouped[day]
        total_records = bucket["total_records"]
        rows.append(
            {
                **bucket,
                "attendance_rate": round((bucket["attended_count"] / total_records) * 100, 2)
                if total_records > 0
                else 0.0,
            }
        )

    return {"rows": rows}


@router.get("/attendance/by-time-block")
def get_attendance_by_time_block_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
    )
    attendance_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=[student.id for student in students],
        event_ids=[event.id for event in events],
    )

    time_block_order = ["early_morning", "morning", "afternoon", "evening", "night", "unknown"]
    grouped: dict[str, dict[str, Any]] = {
        block: {
            "time_block": block,
            "total_checkins": 0,
            "late_count": 0,
            "attended_count": 0,
        }
        for block in time_block_order
    }

    for attendance in attendance_rows:
        block = _resolve_time_block(attendance.time_in)
        bucket = grouped[block]
        bucket["total_checkins"] += 1
        if _attendance_is_valid_value(attendance):
            bucket["attended_count"] += 1
        if _attendance_display_status_value(attendance) == "late":
            bucket["late_count"] += 1

    rows = []
    for block in time_block_order:
        bucket = grouped[block]
        total_checkins = bucket["total_checkins"]
        rows.append(
            {
                **bucket,
                "late_rate": round((bucket["late_count"] / total_checkins) * 100, 2)
                if total_checkins > 0
                else 0.0,
            }
        )

    return {"rows": rows}


@router.get("/attendance/year-level-distribution")
def get_year_level_attendance_distribution_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
    )
    attendance_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=[student.id for student in students],
        event_ids=[event.id for event in events],
    )
    metrics = _group_student_metrics(students, attendance_rows)

    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "year_level": None,
            "student_count": 0,
            "total_records": 0,
            "attended_count": 0,
            "late_count": 0,
            "incomplete_count": 0,
            "absent_count": 0,
            "excused_count": 0,
        }
    )
    for row in metrics:
        year_level = row["year_level"] if row["year_level"] is not None else "Unspecified"
        bucket = grouped[str(year_level)]
        bucket["year_level"] = year_level
        bucket["student_count"] += 1
        bucket["total_records"] += row["total_events"]
        bucket["attended_count"] += row["attended_count"]
        bucket["late_count"] += row["late_count"]
        bucket["incomplete_count"] += row["incomplete_count"]
        bucket["absent_count"] += row["absent_count"]
        bucket["excused_count"] += row["excused_count"]

    rows = sorted(
        grouped.values(),
        key=lambda row: (999 if row["year_level"] == "Unspecified" else int(row["year_level"])),
    )
    for row in rows:
        total_records = row["total_records"]
        row["attendance_rate"] = round((row["attended_count"] / total_records) * 100, 2) if total_records > 0 else 0.0

    return {"rows": rows}


def _participation_bucket(total_events: int) -> str:
    if total_events <= 0:
        return "0"
    if total_events <= 4:
        return str(total_events)
    if total_events <= 9:
        return "5-9"
    return "10+"


@router.get("/attendance/repeat-participation")
def get_repeat_participation_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
    )
    attendance_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=[student.id for student in students],
        event_ids=[event.id for event in events],
    )
    metrics = _group_student_metrics(students, attendance_rows)

    distribution_counts: dict[str, int] = defaultdict(int)
    total_events_sum = 0
    for row in metrics:
        total_events = int(row["total_events"])
        total_events_sum += total_events
        distribution_counts[_participation_bucket(total_events)] += 1

    ordered_buckets = ["0", "1", "2", "3", "4", "5-9", "10+"]
    rows = [
        {
            "participation_bucket": bucket,
            "student_count": distribution_counts.get(bucket, 0),
        }
        for bucket in ordered_buckets
    ]
    average_events = round((total_events_sum / len(metrics)), 2) if metrics else 0.0

    return {
        "rows": rows,
        "average_events_per_student": average_events,
        "students_sample": sorted(
            metrics,
            key=lambda row: (-row["total_events"], -row["attendance_rate"], row["full_name"].lower()),
        )[:100],
    }


@router.get("/events/first-time-vs-repeat")
def get_first_time_vs_repeat_attendee_report(
    event_id: int | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students, events, latest_map = _load_event_participation_dataset(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
        event_id=event_id,
    )
    if event_id is not None and not events:
        raise HTTPException(status_code=404, detail="Event not found")

    student_ids = [student.id for student in students]
    if not student_ids:
        return {"rows": []}

    first_seen_query = (
        db.query(
            AttendanceModel.student_id,
            func.min(Event.start_datetime).label("first_attendance_at"),
        )
        .join(Event, AttendanceModel.event_id == Event.id)
        .filter(
            Event.school_id == school_id,
            AttendanceModel.student_id.in_(student_ids),
        )
    )
    if governance_units:
        allowed_event_ids = _get_event_ids_in_attendance_scope(
            db,
            school_id=school_id,
            governance_units=governance_units,
        )
        if not allowed_event_ids:
            return {"rows": []}
        first_seen_query = first_seen_query.filter(Event.id.in_(allowed_event_ids))

    first_seen_rows = first_seen_query.group_by(AttendanceModel.student_id).all()
    first_seen_by_student = {
        student_id: first_attendance_at
        for student_id, first_attendance_at in first_seen_rows
    }

    rows = []
    for event in events:
        event_attendees = [
            student_id
            for student_id in student_ids
            if (student_id, event.id) in latest_map
        ]
        unique_attendees = sorted(set(event_attendees))
        first_time_count = 0
        repeat_count = 0
        for student_id in unique_attendees:
            first_seen_at = first_seen_by_student.get(student_id)
            if first_seen_at is None or event.start_datetime is None or first_seen_at >= event.start_datetime:
                first_time_count += 1
            else:
                repeat_count += 1

        total_attendees = len(unique_attendees)
        rows.append(
            {
                "event_id": event.id,
                "event_name": event.name,
                "event_date": event.start_datetime.isoformat() if event.start_datetime else None,
                "total_attendees": total_attendees,
                "first_time_count": first_time_count,
                "repeat_count": repeat_count,
                "first_time_rate": round((first_time_count / total_attendees) * 100, 2)
                if total_attendees > 0
                else 0.0,
                "repeat_rate": round((repeat_count / total_attendees) * 100, 2)
                if total_attendees > 0
                else 0.0,
            }
        )

    rows.sort(key=lambda row: (-row["first_time_rate"], row["event_name"].lower()))
    return {"rows": rows}


@router.get("/school/kpi-dashboard")
def get_school_kpi_dashboard_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    department_id: int | None = Query(default=None),
    program_id: int | None = Query(default=None),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    school_id, governance_units, _ = _resolve_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    start_datetime, end_datetime = _validate_date_range(start_date, end_date)

    students = _load_scoped_students(
        db,
        school_id=school_id,
        governance_units=governance_units,
        department_id=department_id,
        program_id=program_id,
    )
    events = _load_scoped_events(
        db,
        school_id=school_id,
        governance_units=governance_units,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        department_id=department_id,
        program_id=program_id,
    )
    attendance_rows = _load_latest_attendance_records(
        db,
        school_id=school_id,
        student_ids=[student.id for student in students],
        event_ids=[event.id for event in events],
    )

    status_counts = {
        "present": 0,
        "late": 0,
        "absent": 0,
        "excused": 0,
        "incomplete": 0,
    }
    attended_count = 0
    for attendance in attendance_rows:
        display_status = _attendance_display_status_value(attendance)
        if display_status in status_counts:
            status_counts[display_status] += 1
        if _attendance_is_valid_value(attendance):
            attended_count += 1

    total_records = len(attendance_rows)
    unique_students_with_records = len({attendance.student_id for attendance in attendance_rows})
    total_students = len(students)

    attendance_rate = round((attended_count / total_records) * 100, 2) if total_records > 0 else 0.0
    late_rate = round((status_counts["late"] / total_records) * 100, 2) if total_records > 0 else 0.0
    absent_rate = round((status_counts["absent"] / total_records) * 100, 2) if total_records > 0 else 0.0
    incomplete_rate = round((status_counts["incomplete"] / total_records) * 100, 2) if total_records > 0 else 0.0
    participation_reach = (
        round((unique_students_with_records / total_students) * 100, 2)
        if total_students > 0
        else 0.0
    )

    return {
        "summary": {
            "total_students_in_scope": total_students,
            "total_events_in_scope": len(events),
            "total_attendance_records": total_records,
            "attended_count": attended_count,
            "late_count": status_counts["late"],
            "absent_count": status_counts["absent"],
            "excused_count": status_counts["excused"],
            "incomplete_count": status_counts["incomplete"],
            "attendance_rate": attendance_rate,
            "late_rate": late_rate,
            "absent_rate": absent_rate,
            "incomplete_rate": incomplete_rate,
            "participation_reach": participation_reach,
            "unique_students_with_records": unique_students_with_records,
        },
        "rows": [
            {"metric": "Attendance Rate", "value": attendance_rate},
            {"metric": "Late Rate", "value": late_rate},
            {"metric": "Absent Rate", "value": absent_rate},
            {"metric": "Incomplete Rate", "value": incomplete_rate},
            {"metric": "Participation Reach", "value": participation_reach},
        ],
    }

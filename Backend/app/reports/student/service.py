"""Business logic for student-focused reports."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_school_id_or_403, has_any_role
from app.models.governance_hierarchy import GovernanceUnitType
from app.models.user import User as UserModel
from app.schemas.attendance import (
    AttendanceStatus,
    StudentAttendanceReport,
    StudentAttendanceResponse,
    StudentAttendanceSummary,
    StudentListItem,
)
from app.services.attendance_status import (
    empty_attendance_display_status_counts,
    empty_attendance_status_counts,
    normalize_attendance_status,
)
from app.routers.attendance.shared import (
    _attendance_display_status_value,
    _attendance_is_valid_value,
    _attendance_matches_status_filter,
    _build_student_attendance_detail,
    _build_student_attendance_record,
    _ensure_attendance_operator_access,
    _ensure_attendance_report_access,
    _ensure_student_in_attendance_scope,
    _get_attendance_governance_units,
    _get_event_ids_in_attendance_scope,
)

from . import queries

logger = logging.getLogger(__name__)


def get_students_attendance_overview(
    db: Session,
    *,
    skip: int,
    limit: int,
    search: Optional[str],
    department_id: Optional[int],
    program_id: Optional[int],
    start_date: Optional[date],
    end_date: Optional[date],
    governance_context: Optional[GovernanceUnitType],
    current_user: UserModel,
) -> list[StudentListItem]:
    _ensure_attendance_report_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    allowed_event_ids = _get_event_ids_in_attendance_scope(
        db,
        school_id=school_id,
        governance_units=governance_units,
    )

    try:
        logger.debug(
            "Building student attendance overview",
            extra={
                "start_date": str(start_date) if start_date else None,
                "end_date": str(end_date) if end_date else None,
                "department_id": department_id,
                "program_id": program_id,
                "search": search,
            },
        )

        base_query = queries.build_students_overview_base_query(
            db,
            school_id=school_id,
            governance_units=governance_units,
            department_id=department_id,
            program_id=program_id,
            search=search,
        )
        total_students = queries.count_students(base_query)
        logger.debug("Student attendance overview matched %s students", total_students)

        students = queries.list_students_overview_page(base_query, skip=skip, limit=limit)
        logger.debug("Loaded %s students for attendance overview page", len(students))

        if not students:
            return []

        student_ids = [student.id for student in students]

        attendance_stats: dict[int, dict[str, Any]] = {}
        event_counts: dict[int, int] = {}

        try:
            attendance_results = queries.list_attendances_for_students_overview(
                db,
                student_ids=student_ids,
                school_id=school_id,
                governance_units=governance_units,
                allowed_event_ids=allowed_event_ids,
                start_date=start_date,
                end_date=end_date,
            )
            logger.debug(
                "Attendance overview aggregate query returned %s rows",
                len(attendance_results),
            )

            latest_by_student_and_event = {}
            for attendance in attendance_results:
                latest_by_student_and_event.setdefault(
                    (attendance.student_id, attendance.event_id),
                    attendance,
                )

            grouped_attendances = {}
            for attendance in latest_by_student_and_event.values():
                grouped_attendances.setdefault(attendance.student_id, []).append(attendance)

            for student_id_value, student_attendances in grouped_attendances.items():
                attendance_stats[student_id_value] = {
                    "attended": sum(
                        1 for attendance in student_attendances if _attendance_is_valid_value(attendance)
                    ),
                    "last_attendance": max(
                        (attendance.time_in for attendance in student_attendances if attendance.time_in),
                        default=None,
                    ),
                }
                event_counts[student_id_value] = len(student_attendances)
        except Exception:
            logger.exception("Attendance overview aggregate query failed")
            attendance_stats = {}
            event_counts = {}

        result: list[StudentListItem] = []
        for student in students:
            try:
                stats = attendance_stats.get(student.id, {"attended": 0, "last_attendance": None})
                attended = int(stats["attended"])
                last_attendance = stats["last_attendance"]
                total_events = int(event_counts.get(student.id, 0))

                first_name = getattr(student.user, "first_name", "") or ""
                middle_name = getattr(student.user, "middle_name", "") or ""
                last_name = getattr(student.user, "last_name", "") or ""
                middle_part = f"{middle_name} " if middle_name else ""
                full_name = f"{first_name} {middle_part}{last_name}".strip()

                attendance_rate = round((attended / total_events * 100) if total_events > 0 else 0, 2)
                result.append(
                    StudentListItem(
                        id=student.id,
                        student_id=student.student_id,
                        full_name=full_name,
                        department_name=getattr(student.department, "name", None) if student.department else None,
                        program_name=getattr(student.program, "name", None) if student.program else None,
                        year_level=student.year_level,
                        total_events=total_events,
                        attendance_rate=attendance_rate,
                        last_attendance=last_attendance,
                    )
                )
            except Exception:
                logger.exception("Failed to process attendance overview row", extra={"student_id": student.id})
                continue

        logger.debug("Returning %s student attendance overview rows", len(result))
        return result
    except Exception as exc:
        logger.exception("Attendance overview request failed")
        raise HTTPException(500, f"Database error: {str(exc)}") from exc


def get_student_attendance_report(
    db: Session,
    *,
    student_id: int,
    start_date: Optional[date],
    end_date: Optional[date],
    status: Optional[AttendanceStatus],
    event_type: Optional[str],
    governance_context: Optional[GovernanceUnitType],
    current_user: UserModel,
) -> StudentAttendanceReport:
    can_view_own_records = (
        has_any_role(current_user, ["student"])
        and current_user.student_profile is not None
        and current_user.student_profile.id == student_id
    )
    if not can_view_own_records:
        _ensure_attendance_report_access(db, current_user)

    school_id = get_school_id_or_403(current_user)
    governance_units = (
        []
        if can_view_own_records
        else _get_attendance_governance_units(
            db,
            current_user=current_user,
            governance_context=governance_context,
        )
    )
    allowed_event_ids = _get_event_ids_in_attendance_scope(
        db,
        school_id=school_id,
        governance_units=governance_units,
    )

    student = queries.get_student_profile_for_report(
        db,
        school_id=school_id,
        student_profile_id=student_id,
    )
    if not student:
        raise HTTPException(404, "Student not found")
    _ensure_student_in_attendance_scope(student, governance_units)

    attendances = queries.list_student_attendances_for_report(
        db,
        school_id=school_id,
        student_profile_id=student_id,
        governance_units=governance_units,
        allowed_event_ids=allowed_event_ids,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
    )

    if status is not None:
        attendances = [attendance for attendance in attendances if _attendance_matches_status_filter(attendance, status)]

    total_attended = len([attendance for attendance in attendances if _attendance_is_valid_value(attendance)])
    total_late = len(
        [
            attendance
            for attendance in attendances
            if _attendance_display_status_value(attendance) == AttendanceStatus.LATE.value
            and _attendance_is_valid_value(attendance)
        ]
    )
    total_incomplete = len(
        [attendance for attendance in attendances if _attendance_display_status_value(attendance) == AttendanceStatus.INCOMPLETE.value]
    )
    total_absent = len(
        [attendance for attendance in attendances if _attendance_display_status_value(attendance) == AttendanceStatus.ABSENT.value]
    )
    total_excused = len(
        [attendance for attendance in attendances if _attendance_display_status_value(attendance) == AttendanceStatus.EXCUSED.value]
    )
    total_events = len(attendances)

    attendance_rate = (total_attended / total_events * 100) if total_events > 0 else 0
    last_attendance = max([attendance.time_in for attendance in attendances if attendance.time_in]) if attendances else None

    middle_name = student.user.middle_name
    full_name = f"{student.user.first_name} {middle_name + ' ' if middle_name else ''}{student.user.last_name}"

    summary = StudentAttendanceSummary(
        student_id=student.student_id,
        student_name=full_name,
        total_events=total_events,
        attended_events=total_attended,
        late_events=total_late,
        incomplete_events=total_incomplete,
        absent_events=total_absent,
        excused_events=total_excused,
        attendance_rate=round(attendance_rate, 2),
        last_attendance=last_attendance,
    )

    attendance_records = [_build_student_attendance_detail(attendance) for attendance in attendances]

    monthly_stats = {}
    for attendance in attendances:
        if attendance.event and attendance.event.start_datetime:
            month_key = attendance.event.start_datetime.strftime("%Y-%m")
            if month_key not in monthly_stats:
                monthly_stats[month_key] = empty_attendance_display_status_counts()
            status_value = _attendance_display_status_value(attendance)
            monthly_stats[month_key][status_value] = monthly_stats[month_key].get(status_value, 0) + 1

    event_type_stats = {}
    for attendance in attendances:
        if attendance.event:
            attendance_event_type = getattr(attendance.event, "event_type", "Regular Events")
            event_type_stats[attendance_event_type] = event_type_stats.get(attendance_event_type, 0) + 1

    return StudentAttendanceReport(
        student=summary,
        attendance_records=attendance_records,
        monthly_stats=monthly_stats,
        event_type_stats=event_type_stats,
    )


def get_student_attendance_stats(
    db: Session,
    *,
    student_id: int,
    start_date: Optional[date],
    end_date: Optional[date],
    group_by: Optional[str],
    current_user: UserModel,
) -> dict[str, Any]:
    can_view_own_records = (
        has_any_role(current_user, ["student"])
        and current_user.student_profile is not None
        and current_user.student_profile.id == student_id
    )
    if not can_view_own_records:
        _ensure_attendance_report_access(db, current_user)
    school_id = get_school_id_or_403(current_user)

    if not queries.student_exists_in_school(
        db,
        school_id=school_id,
        student_profile_id=student_id,
    ):
        raise HTTPException(404, "Student not found")

    base_query = queries.build_student_stats_base_query(
        db,
        school_id=school_id,
        student_profile_id=student_id,
        start_date=start_date,
        end_date=end_date,
    )

    status_counts = queries.list_student_status_counts(base_query)
    date_trunc_mapping = {
        "day": "day",
        "week": "week",
        "month": "month",
        "year": "year",
    }
    trunc_period = date_trunc_mapping.get(group_by, "month")
    trend_results = queries.list_student_trend_results(base_query, trunc_period=trunc_period)
    event_type_query = queries.list_student_event_type_breakdown(base_query)

    status_distribution = empty_attendance_status_counts()
    for status_value, count in status_counts:
        status_distribution[normalize_attendance_status(status_value)] = int(count)

    return {
        "status_distribution": status_distribution,
        "trend_data": [
            {
                "period": row.period.strftime(
                    "%Y-%m-%d" if group_by == "day"
                    else "%Y-%m" if group_by == "month"
                    else "%Y-%U" if group_by == "week"
                    else "%Y"
                ) if row.period else None,
                "status": normalize_attendance_status(row.status),
                "count": row.count,
            }
            for row in trend_results
        ],
        "event_type_breakdown": [
            {
                "event_type": row.type or "Unknown",
                "status": normalize_attendance_status(row.status),
                "count": row.count,
            }
            for row in event_type_query
        ],
        "date_range": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "group_by": group_by,
        },
    }


def get_all_student_attendance_records(
    db: Session,
    *,
    student_ids: list[str] | None,
    event_id: int | None,
    status: AttendanceStatus | None,
    skip: int,
    limit: int,
    current_user: UserModel,
) -> list[StudentAttendanceResponse]:
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)

    results = queries.list_all_student_record_rows(
        db,
        school_id=school_id,
        student_ids=student_ids,
        event_id=event_id,
        skip=skip,
        limit=limit,
    )

    student_records = {}
    for attendance, student_id, first_name, last_name, event_name in results:
        if not _attendance_matches_status_filter(attendance, status):
            continue

        record = _build_student_attendance_record(
            attendance,
            event_name=event_name,
        )
        if student_id not in student_records:
            student_records[student_id] = {
                "student_id": student_id,
                "student_name": f"{first_name} {last_name}",
                "attendances": [],
            }
        student_records[student_id]["attendances"].append(record)

    response = []
    for student_id_value, data in student_records.items():
        response.append(
            StudentAttendanceResponse(
                student_id=student_id_value,
                student_name=data["student_name"],
                total_records=len(data["attendances"]),
                attendances=data["attendances"],
            )
        )
    return response


def get_student_attendance_records(
    db: Session,
    *,
    student_id: str,
    event_id: int | None,
    status: AttendanceStatus | None,
    skip: int,
    limit: int,
    current_user: UserModel,
) -> StudentAttendanceResponse:
    if (
        has_any_role(current_user, ["student"])
        and current_user.student_profile
        and current_user.student_profile.student_id != student_id
    ):
        raise HTTPException(403, "Can only view your own records")

    school_id = get_school_id_or_403(current_user)
    student = queries.get_student_profile_by_student_code(
        db,
        school_id=school_id,
        student_id=student_id,
    )
    if not student:
        raise HTTPException(404, "Student not found")

    results = queries.list_student_record_rows(
        db,
        school_id=school_id,
        student_profile_id=student.id,
        event_id=event_id,
        skip=skip,
        limit=limit,
    )

    attendances = []
    for attendance, event_name in results:
        if not _attendance_matches_status_filter(attendance, status):
            continue
        attendances.append(
            _build_student_attendance_record(
                attendance,
                event_name=event_name,
            )
        )

    return StudentAttendanceResponse(
        student_id=student_id,
        student_name=f"{student.user.first_name} {student.user.last_name}",
        total_records=len(attendances),
        attendances=attendances,
    )


def get_my_attendance_records(
    db: Session,
    *,
    event_id: int | None,
    status: AttendanceStatus | None,
    skip: int,
    limit: int,
    current_user: UserModel,
) -> list[StudentAttendanceResponse]:
    if not current_user.student_profile:
        raise HTTPException(
            status_code=403,
            detail="Only students can access their own attendance records",
        )

    school_id = get_school_id_or_403(current_user)
    student = current_user.student_profile
    results = queries.list_student_record_rows(
        db,
        school_id=school_id,
        student_profile_id=student.id,
        event_id=event_id,
        skip=skip,
        limit=limit,
    )

    attendances = []
    for attendance, event_name in results:
        if not _attendance_matches_status_filter(attendance, status):
            continue
        attendances.append(
            _build_student_attendance_record(
                attendance,
                event_name=event_name,
            )
        )

    return [
        StudentAttendanceResponse(
            student_id=student.student_id,
            student_name=f"{current_user.first_name} {current_user.last_name}",
            total_records=len(attendances),
            attendances=attendances,
        )
    ]


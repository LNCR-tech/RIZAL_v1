"""Business logic for school-level attendance reports."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.core.security import get_school_id_or_403
from app.models.attendance import Attendance as AttendanceModel
from app.models.user import User as UserModel
from app.routers.attendance.shared import _ensure_attendance_report_access

from . import queries


def _build_student_full_name(user: UserModel | None) -> str:
    if user is None:
        return "Unknown Student"
    return " ".join(
        part.strip()
        for part in [
            getattr(user, "first_name", "") or "",
            getattr(user, "middle_name", "") or "",
            getattr(user, "last_name", "") or "",
        ]
        if part and part.strip()
    ) or getattr(user, "email", "Unknown Student")


def get_attendance_summary(
    db: Session,
    *,
    start_date: date | None,
    end_date: date | None,
    department_id: int | None,
    program_id: int | None,
    current_user: UserModel,
) -> dict[str, Any]:
    _ensure_attendance_report_access(db, current_user)
    school_id = get_school_id_or_403(current_user)

    query = queries.build_attendance_summary_query(
        db,
        school_id=school_id,
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        program_id=program_id,
    )

    total_records = query.count()
    present_count = query.filter(AttendanceModel.status == "present").count()
    late_count = query.filter(AttendanceModel.status == "late").count()
    absent_count = query.filter(AttendanceModel.status == "absent").count()
    excused_count = query.filter(AttendanceModel.status == "excused").count()
    attended_count = present_count + late_count

    unique_students = query.with_entities(AttendanceModel.student_id).distinct().count()
    unique_events = query.with_entities(AttendanceModel.event_id).distinct().count()

    student_profiles = queries.list_student_profiles_for_login_report(
        db,
        school_id=school_id,
        department_id=department_id,
        program_id=program_id,
    )
    login_stats_by_user = queries.get_successful_student_login_stats(
        db,
        school_id=school_id,
        user_ids=[profile.user_id for profile in student_profiles if profile.user_id is not None],
        start_date=start_date,
        end_date=end_date,
    )

    student_login_rows: list[dict[str, Any]] = []
    logged_in_students = 0
    for profile in student_profiles:
        login_stats = login_stats_by_user.get(profile.user_id, {})
        successful_login_count = int(login_stats.get("successful_login_count", 0) or 0)
        has_logged_in = successful_login_count > 0
        if has_logged_in:
            logged_in_students += 1

        student_login_rows.append({
            "student_profile_id": profile.id,
            "user_id": profile.user_id,
            "student_id": profile.student_id,
            "full_name": _build_student_full_name(profile.user),
            "department_name": getattr(profile.department, "name", None) if profile.department else None,
            "program_name": getattr(profile.program, "name", None) if profile.program else None,
            "year_level": profile.year_level,
            "has_logged_in": has_logged_in,
            "successful_login_count": successful_login_count,
            "last_login_at": login_stats.get("last_login_at"),
        })

    total_students_in_scope = len(student_profiles)
    not_logged_in_students = max(total_students_in_scope - logged_in_students, 0)

    return {
        "summary": {
            "total_attendance_records": total_records,
            "present_count": present_count,
            "late_count": late_count,
            "attended_count": attended_count,
            "absent_count": absent_count,
            "excused_count": excused_count,
            "attendance_rate": round((attended_count / total_records * 100) if total_records > 0 else 0, 2),
            "unique_students": unique_students,
            "unique_events": unique_events,
        },
        "filters_applied": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "department_id": department_id,
            "program_id": program_id,
        },
        "student_login_summary": {
            "total_students": total_students_in_scope,
            "logged_in_students": logged_in_students,
            "not_logged_in_students": not_logged_in_students,
            "login_coverage_rate": round(
                (logged_in_students / total_students_in_scope * 100)
                if total_students_in_scope > 0
                else 0,
                2,
            ),
        },
        "student_login_rows": student_login_rows,
    }

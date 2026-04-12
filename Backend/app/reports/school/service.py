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
    }

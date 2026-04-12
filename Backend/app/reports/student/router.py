"""Router layer for student-focused reports."""

from __future__ import annotations

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.governance_hierarchy import GovernanceUnitType
from app.models.user import User as UserModel
from app.schemas.attendance import (
    AttendanceStatus,
    StudentAttendanceReport,
    StudentAttendanceResponse,
    StudentListItem,
)

from . import service

router = APIRouter()


@router.get("/students/overview", response_model=List[StudentListItem])
async def get_students_attendance_overview(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    department_id: Optional[int] = Query(None),
    program_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    governance_context: Optional[GovernanceUnitType] = Query(None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_students_attendance_overview(
        db,
        skip=skip,
        limit=limit,
        search=search,
        department_id=department_id,
        program_id=program_id,
        start_date=start_date,
        end_date=end_date,
        governance_context=governance_context,
        current_user=current_user,
    )


@router.get("/students/{student_id}/report", response_model=StudentAttendanceReport)
def get_student_attendance_report(
    student_id: int,
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    status: Optional[AttendanceStatus] = Query(None, description="Filter by attendance status"),
    event_type: Optional[str] = Query(None, description="Filter by event type/category"),
    governance_context: Optional[GovernanceUnitType] = Query(None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_student_attendance_report(
        db,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        event_type=event_type,
        governance_context=governance_context,
        current_user=current_user,
    )


@router.get("/students/{student_id}/stats")
def get_student_attendance_stats(
    student_id: int,
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    group_by: Optional[str] = Query("month", description="Group by: month, week, day"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return service.get_student_attendance_stats(
        db,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by,
        current_user=current_user,
    )


@router.get("/students/records", response_model=List[StudentAttendanceResponse])
def get_all_student_attendance_records(
    student_ids: List[str] = Query(None, description="Filter by specific student IDs"),
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    status: Optional[AttendanceStatus] = Query(None, description="Filter by status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return service.get_all_student_attendance_records(
        db,
        student_ids=student_ids,
        event_id=event_id,
        status=status,
        skip=skip,
        limit=limit,
        current_user=current_user,
    )


@router.get("/students/{student_id}/records", response_model=StudentAttendanceResponse)
def get_student_attendance_records(
    student_id: str,
    event_id: Optional[int] = Query(None),
    status: Optional[AttendanceStatus] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return service.get_student_attendance_records(
        db,
        student_id=student_id,
        event_id=event_id,
        status=status,
        skip=skip,
        limit=limit,
        current_user=current_user,
    )


@router.get("/me/records", response_model=List[StudentAttendanceResponse])
def get_my_attendance_records(
    current_user: UserModel = Depends(get_current_user),
    event_id: Optional[int] = Query(None),
    status: Optional[AttendanceStatus] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return service.get_my_attendance_records(
        db,
        event_id=event_id,
        status=status,
        skip=skip,
        limit=limit,
        current_user=current_user,
    )


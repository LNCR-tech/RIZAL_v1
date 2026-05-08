"""Router layer for attendance event-level reports."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.governance_hierarchy import GovernanceUnitType
from app.models.user import User as UserModel
from app.schemas.attendance import Attendance, AttendanceReportResponse, AttendanceStatus, AttendanceWithStudent

from . import service

router = APIRouter()


@router.get("/events/{event_id}/report", response_model=AttendanceReportResponse)
def get_event_attendance_report(
    event_id: int,
    year_level: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    program_id: Optional[int] = Query(None),
    status: Optional[AttendanceStatus] = Query(None),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_event_attendance_report(
        db,
        event_id=event_id,
        year_level=year_level,
        department_id=department_id,
        program_id=program_id,
        status_filter=status,
        governance_context=governance_context,
        current_user=current_user,
    )


@router.get("/events/{event_id}/attendees", response_model=List[Attendance])
def get_event_attendees(
    event_id: int,
    year_level: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    program_id: Optional[int] = Query(None),
    status: Optional[AttendanceStatus] = None,
    skip: int = 0,
    limit: int = 100,
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_event_attendees(
        db,
        event_id=event_id,
        year_level=year_level,
        department_id=department_id,
        program_id=program_id,
        status=status,
        skip=skip,
        limit=limit,
        governance_context=governance_context,
        current_user=current_user,
    )


@router.get("/events/{event_id}/attendances", response_model=List[AttendanceWithStudent])
def get_attendances_by_event(
    event_id: int,
    active_only: bool = Query(True, description="Only show active attendances (no time_out)"),
    year_level: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    program_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return service.get_attendances_by_event(
        db,
        event_id=event_id,
        active_only=active_only,
        year_level=year_level,
        department_id=department_id,
        program_id=program_id,
        skip=skip,
        limit=limit,
        governance_context=governance_context,
        current_user=current_user,
    )


@router.get("/events/{event_id}/attendances/{status}", response_model=List[Attendance])
def get_attendances_by_event_and_status(
    event_id: int,
    status: AttendanceStatus,
    skip: int = 0,
    limit: int = 100,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return service.get_attendances_by_event_and_status(
        db,
        event_id=event_id,
        status=status,
        skip=skip,
        limit=limit,
        governance_context=governance_context,
        current_user=current_user,
    )


@router.get("/events/{event_id}/attendances-with-students", response_model=List[AttendanceWithStudent])
def get_attendances_with_students(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return service.get_attendances_with_students(
        db,
        event_id=event_id,
        governance_context=governance_context,
        current_user=current_user,
    )


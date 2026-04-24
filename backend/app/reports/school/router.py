"""Router layer for school-level reports."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User as UserModel

from . import service

router = APIRouter()


@router.get("/summary", response_model=Dict[str, Any])
def get_attendance_summary(
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    department_id: Optional[int] = Query(None),
    program_id: Optional[int] = Query(None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_attendance_summary(
        db,
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        program_id=program_id,
        current_user=current_user,
    )


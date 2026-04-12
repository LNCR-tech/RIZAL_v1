"""Use: Handles audit log viewing API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs audit log viewing features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_admin_or_campus_admin
from app.core.dependencies import get_db
from app.models.user import User
from app.reports.system import router as system_reports_router
from app.schemas.audit import SchoolAuditLogSearchResponse

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("", response_model=SchoolAuditLogSearchResponse)
def search_audit_logs(
    q: Optional[str] = Query(default=None, max_length=200),
    action: Optional[str] = Query(default=None, max_length=100),
    status_value: Optional[str] = Query(default=None, alias="status", max_length=30),
    actor_user_id: Optional[int] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    return system_reports_router.search_audit_logs(
        db,
        current_user=current_user,
        q=q,
        action=action,
        status_value=status_value,
        actor_user_id=actor_user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.security import get_current_user_with_roles, has_any_role
from app.database import get_db
from app.models.school import SchoolAuditLog
from app.models.user import User
from app.schemas.audit import SchoolAuditLogSearchItem, SchoolAuditLogSearchResponse

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


def _resolve_scope(current_user: User) -> Optional[int]:
    is_admin = has_any_role(current_user, ["admin"])
    school_id = getattr(current_user, "school_id", None)
    if is_admin and school_id is None:
        return None
    if school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school.",
        )
    return school_id


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
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    if not has_any_role(current_user, ["admin", "school_IT", "school-it", "school_it"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School IT privileges required",
        )

    school_scope = _resolve_scope(current_user)

    query = db.query(SchoolAuditLog)
    filters = []
    if school_scope is not None:
        filters.append(SchoolAuditLog.school_id == school_scope)
    if action:
        filters.append(SchoolAuditLog.action.ilike(f"%{action.strip()}%"))
    if status_value:
        filters.append(SchoolAuditLog.status.ilike(f"%{status_value.strip()}%"))
    if actor_user_id is not None:
        filters.append(SchoolAuditLog.actor_user_id == actor_user_id)
    if start_date is not None:
        filters.append(SchoolAuditLog.created_at >= start_date)
    if end_date is not None:
        filters.append(SchoolAuditLog.created_at <= end_date)
    if q:
        search = q.strip()
        filters.append(
            or_(
                SchoolAuditLog.action.ilike(f"%{search}%"),
                SchoolAuditLog.status.ilike(f"%{search}%"),
                SchoolAuditLog.details.ilike(f"%{search}%"),
            )
        )

    if filters:
        query = query.filter(and_(*filters))

    total = query.count()
    rows = (
        query.order_by(SchoolAuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items: list[SchoolAuditLogSearchItem] = []
    for row in rows:
        details_json = None
        if row.details:
            try:
                parsed = json.loads(row.details)
                if isinstance(parsed, dict):
                    details_json = parsed
            except Exception:
                details_json = None
        items.append(
            SchoolAuditLogSearchItem(
                id=row.id,
                school_id=row.school_id,
                actor_user_id=row.actor_user_id,
                action=row.action,
                status=row.status,
                details=row.details,
                details_json=details_json,
                created_at=row.created_at,
            )
        )

    return SchoolAuditLogSearchResponse(total=total, items=items)

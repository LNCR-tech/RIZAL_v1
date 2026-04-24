"""Router helpers for system-level report endpoints.

Legacy routers call these handlers to keep endpoint contracts unchanged while
using the reports service/query layers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.audit import SchoolAuditLogSearchResponse
from app.schemas.governance_hierarchy import GovernanceDashboardOverviewResponse
from app.schemas.import_job import ImportJobStatusResponse
from app.schemas.notification import NotificationLogItem

from . import service


def search_audit_logs(
    db: Session,
    *,
    current_user: User,
    q: Optional[str],
    action: Optional[str],
    status_value: Optional[str],
    actor_user_id: Optional[int],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    limit: int,
    offset: int,
) -> SchoolAuditLogSearchResponse:
    return service.search_audit_logs(
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


def list_notification_logs(
    db: Session,
    *,
    current_user: User,
    school_id: int | None,
    category: str | None,
    status_value: str | None,
    user_id: int | None,
    limit: int,
) -> list[NotificationLogItem]:
    return service.list_notification_logs(
        db,
        current_user=current_user,
        school_id=school_id,
        category=category,
        status_value=status_value,
        user_id=user_id,
        limit=limit,
    )


def get_governance_dashboard_overview(
    db: Session,
    *,
    current_user: User,
    governance_unit_id: int,
) -> GovernanceDashboardOverviewResponse:
    return service.get_governance_dashboard_overview(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
    )


def download_preview_errors(
    db: Session,
    *,
    preview_token: str,
    current_user: User,
) -> StreamingResponse:
    return service.download_preview_errors(
        db,
        preview_token=preview_token,
        current_user=current_user,
    )


def download_preview_retry_file(
    db: Session,
    *,
    preview_token: str,
    current_user: User,
) -> StreamingResponse:
    return service.download_preview_retry_file(
        db,
        preview_token=preview_token,
        current_user=current_user,
    )


def get_import_status(
    db: Session,
    *,
    job_id: str,
    current_user: User,
) -> ImportJobStatusResponse:
    return service.get_import_status(
        db,
        job_id=job_id,
        current_user=current_user,
    )


def download_import_errors(
    db: Session,
    *,
    job_id: str,
    current_user: User,
) -> FileResponse:
    return service.download_import_errors(
        db,
        job_id=job_id,
        current_user=current_user,
    )


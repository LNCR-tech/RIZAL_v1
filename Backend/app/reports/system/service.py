"""Business logic for system-level report endpoints."""

from __future__ import annotations

import io
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import has_any_role
from app.models.user import User
from app.schemas.audit import SchoolAuditLogSearchItem, SchoolAuditLogSearchResponse
from app.schemas.governance_hierarchy import GovernanceDashboardOverviewResponse
from app.schemas.import_job import ImportJobStatusResponse
from app.schemas.notification import NotificationLogItem
from app.services import governance_hierarchy_service

from . import queries


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
    school_scope = queries.resolve_audit_scope(
        current_user,
        is_admin=has_any_role(current_user, ["admin"]),
    )
    query = queries.build_audit_logs_query(
        db,
        school_scope=school_scope,
        q=q,
        action=action,
        status_value=status_value,
        actor_user_id=actor_user_id,
        start_date=start_date,
        end_date=end_date,
    )

    total = query.count()
    rows = queries.list_audit_log_rows(query, offset=offset, limit=limit)

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
    actor_school_id = getattr(current_user, "school_id", None)
    is_platform_admin = has_any_role(current_user, ["admin"]) and actor_school_id is None

    query = queries.build_notification_logs_query(
        db,
        actor_school_id=actor_school_id,
        is_platform_admin=is_platform_admin,
        school_id=school_id,
        category=category,
        status_value=status_value,
        user_id=user_id,
    )
    return queries.list_notification_log_rows(query, limit=limit)


def get_governance_dashboard_overview(
    db: Session,
    *,
    current_user: User,
    governance_unit_id: int,
) -> GovernanceDashboardOverviewResponse:
    return governance_hierarchy_service.get_governance_dashboard_overview(
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
    settings = get_settings()
    manifest, _ = queries.load_preview_manifest(
        settings=settings,
        preview_token=preview_token,
        current_user=current_user,
    )
    error_rows = manifest.get("error_rows")
    if not isinstance(error_rows, list) or not error_rows:
        raise HTTPException(status_code=404, detail="No preview errors available to download")

    original_filename = str(manifest.get("original_filename") or "student_import.xlsx")
    report_bytes = queries.build_preview_error_report_bytes(error_rows)
    download_name = f"preview_errors_{Path(original_filename).stem}.xlsx"
    return StreamingResponse(
        io.BytesIO(report_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


def download_preview_retry_file(
    db: Session,
    *,
    preview_token: str,
    current_user: User,
) -> StreamingResponse:
    settings = get_settings()
    manifest, _ = queries.load_preview_manifest(
        settings=settings,
        preview_token=preview_token,
        current_user=current_user,
    )
    error_rows = manifest.get("error_rows")
    if not isinstance(error_rows, list) or not error_rows:
        raise HTTPException(status_code=404, detail="No preview errors available to retry")

    retry_row_payloads = [
        item["row_data"]
        for item in error_rows
        if isinstance(item, dict) and isinstance(item.get("row_data"), dict)
    ]
    if not retry_row_payloads:
        raise HTTPException(
            status_code=404,
            detail="No retryable row payloads found for this preview",
        )

    original_filename = str(manifest.get("original_filename") or "student_import.xlsx")
    retry_bytes = queries.build_retry_workbook_bytes(
        sheet_title="Students-Retry",
        row_payloads=retry_row_payloads,
    )
    download_name = f"preview_retry_{Path(original_filename).name}"
    return StreamingResponse(
        io.BytesIO(retry_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


def get_import_status(
    db: Session,
    *,
    job_id: str,
    current_user: User,
) -> ImportJobStatusResponse:
    return queries.build_import_status_response(
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
    failed_report_path = queries.resolve_failed_import_report_path(
        db,
        job_id=job_id,
        current_user=current_user,
    )
    return FileResponse(
        path=failed_report_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"import_{job_id}_failed_rows.xlsx",
    )

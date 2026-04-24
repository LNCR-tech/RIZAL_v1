"""Query helpers for system-wide report endpoints."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status
from openpyxl import Workbook
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.import_job import BulkImportJob
from app.models.platform_features import NotificationLog
from app.models.school import SchoolAuditLog
from app.models.user import User
from app.repositories.import_repository import ImportRepository
from app.schemas.import_job import ImportErrorItem, ImportJobStatusResponse
from app.services.import_validation_service import EXPECTED_HEADERS


def resolve_audit_scope(current_user: User, *, is_admin: bool) -> Optional[int]:
    school_id = getattr(current_user, "school_id", None)
    if is_admin and school_id is None:
        return None
    if school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school.",
        )
    return school_id


def build_audit_logs_query(
    db: Session,
    *,
    school_scope: int | None,
    q: str | None,
    action: str | None,
    status_value: str | None,
    actor_user_id: int | None,
    start_date,
    end_date,
):
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
    return query


def list_audit_log_rows(query, *, offset: int, limit: int):
    return (
        query.order_by(SchoolAuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def build_notification_logs_query(
    db: Session,
    *,
    actor_school_id: int | None,
    is_platform_admin: bool,
    school_id: int | None,
    category: str | None,
    status_value: str | None,
    user_id: int | None,
):
    query = db.query(NotificationLog)
    if not is_platform_admin:
        if actor_school_id is None:
            raise HTTPException(status_code=403, detail="User is not assigned to a school")
        query = query.filter(NotificationLog.school_id == actor_school_id)
    elif school_id is not None:
        query = query.filter(NotificationLog.school_id == school_id)

    if category:
        query = query.filter(NotificationLog.category == category)
    if status_value:
        query = query.filter(NotificationLog.status == status_value)
    if user_id is not None:
        query = query.filter(NotificationLog.user_id == user_id)
    return query


def list_notification_log_rows(query, *, limit: int):
    return query.order_by(NotificationLog.created_at.desc()).limit(limit).all()


def ensure_user_school(current_user: User) -> int:
    school_id = getattr(current_user, "school_id", None)
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )
    return int(school_id)


def preview_manifest_dir(settings) -> Path:
    return Path(settings.import_storage_dir) / "previews"


def preview_manifest_path(settings, preview_token: str) -> Path:
    return preview_manifest_dir(settings) / f"{preview_token}.json"


def load_preview_manifest(
    *,
    settings,
    preview_token: str,
    current_user: User,
) -> tuple[dict, Path]:
    manifest_path = preview_manifest_path(settings, preview_token)
    if not manifest_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Approved preview not found. Preview the file again before importing.",
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Approved preview data is invalid. Preview the file again before importing.",
        ) from exc

    if manifest.get("created_by_user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Approved preview not found")

    target_school_id = ensure_user_school(current_user)
    if manifest.get("target_school_id") != target_school_id:
        raise HTTPException(status_code=404, detail="Approved preview not found")

    if not isinstance(manifest.get("rows"), list):
        raise HTTPException(
            status_code=400,
            detail="Approved preview data is incomplete. Preview the file again before importing.",
        )
    return manifest, manifest_path


def build_retry_workbook_bytes(*, sheet_title: str, row_payloads: list[dict]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title
    sheet.append(EXPECTED_HEADERS)
    for row_data in row_payloads:
        sheet.append([str(row_data.get(header, "")) for header in EXPECTED_HEADERS])

    output = io.BytesIO()
    workbook.save(output)
    workbook.close()
    output.seek(0)
    return output.read()


def build_preview_error_report_bytes(error_payloads: list[dict]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Preview Errors"
    sheet.append(EXPECTED_HEADERS + ["Error"])
    for item in error_payloads:
        row_data = item.get("row_data") if isinstance(item.get("row_data"), dict) else {}
        error_message = "; ".join(item.get("errors") or []) or "Unknown preview error"
        sheet.append([str(row_data.get(header, "")) for header in EXPECTED_HEADERS] + [error_message])

    output = io.BytesIO()
    workbook.save(output)
    workbook.close()
    output.seek(0)
    return output.read()


def get_import_job_for_user(
    db: Session,
    *,
    job_id: str,
    user_id: int,
) -> BulkImportJob:
    repo = ImportRepository(db)
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    if job.created_by_user_id != user_id:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job


def build_import_status_response(
    db: Session,
    *,
    job_id: str,
    current_user: User,
) -> ImportJobStatusResponse:
    repo = ImportRepository(db)
    job = get_import_job_for_user(db, job_id=job_id, user_id=current_user.id)

    percentage = 0.0
    if job.total_rows > 0:
        percentage = round((job.processed_rows / job.total_rows) * 100, 2)

    errors = [
        ImportErrorItem(row=item.row_number, error=item.error_message)
        for item in repo.fetch_errors(job_id, limit=5000)
    ]

    failed_report_download_url = None
    if job.failed_report_path:
        failed_report_download_url = f"/api/admin/import-errors/{job_id}/download"

    return ImportJobStatusResponse(
        job_id=job.id,
        state=job.status,
        total_rows=job.total_rows,
        processed_rows=job.processed_rows,
        success_count=job.success_count,
        failed_count=job.failed_count,
        percentage_completed=percentage,
        estimated_time_remaining_seconds=job.eta_seconds,
        errors=errors,
        failed_report_download_url=failed_report_download_url,
    )


def resolve_failed_import_report_path(
    db: Session,
    *,
    job_id: str,
    current_user: User,
) -> str:
    job = get_import_job_for_user(db, job_id=job_id, user_id=current_user.id)
    if not job.failed_report_path:
        raise HTTPException(status_code=404, detail="No failed row report available for this job")
    if not os.path.exists(job.failed_report_path):
        raise HTTPException(status_code=404, detail="Failed row report file no longer exists")
    return str(job.failed_report_path)


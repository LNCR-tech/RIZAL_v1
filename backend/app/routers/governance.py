"""Use: Handles governance settings, members, and announcements API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs governance settings, members, and announcements features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.timezones import utc_now
from app.core.security import (
    get_current_admin_or_campus_admin,
    get_current_application_user,
    has_any_role,
)
from app.core.dependencies import get_db
from app.models.import_job import BulkImportJob
from app.models.platform_features import (
    DataGovernanceSetting,
    DataRequest,
    DataRetentionRunLog,
    UserPrivacyConsent,
)
from app.models.notifications import NotificationLog
from app.models.school import SchoolAuditLog
from app.models.user import User
from app.schemas.governance import (
    DataGovernanceSettingResponse,
    DataGovernanceSettingUpdate,
    DataRequestCreate,
    DataRequestItem,
    DataRequestStatusUpdate,
    PrivacyConsentCreate,
    PrivacyConsentItem,
    RetentionRunRequest,
    RetentionRunResult,
)

router = APIRouter(prefix="/api/governance", tags=["governance"])


def _resolve_school_id(current_user: User, requested_school_id: int | None = None) -> int:
    actor_school_id = getattr(current_user, "school_id", None)
    is_platform_admin = has_any_role(current_user, ["admin"]) and actor_school_id is None
    if is_platform_admin:
        if requested_school_id is None:
            raise HTTPException(status_code=400, detail="school_id is required for platform admin")
        return requested_school_id
    if actor_school_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a school")
    return actor_school_id


def _get_or_create_setting(db: Session, school_id: int) -> DataGovernanceSetting:
    setting = (
        db.query(DataGovernanceSetting)
        .filter(DataGovernanceSetting.school_id == school_id)
        .first()
    )
    if setting:
        return setting
    setting = DataGovernanceSetting(school_id=school_id)
    db.add(setting)
    db.flush()
    return setting


@router.get("/settings/me", response_model=DataGovernanceSettingResponse)
def get_governance_settings(
    school_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    scoped_school_id = _resolve_school_id(current_user, school_id)
    setting = _get_or_create_setting(db, scoped_school_id)
    db.commit()
    db.refresh(setting)
    return setting


@router.put("/settings/me", response_model=DataGovernanceSettingResponse)
def update_governance_settings(
    payload: DataGovernanceSettingUpdate,
    school_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    scoped_school_id = _resolve_school_id(current_user, school_id)
    setting = _get_or_create_setting(db, scoped_school_id)

    for field in [
        "attendance_retention_days",
        "audit_log_retention_days",
        "import_file_retention_days",
        "auto_delete_enabled",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(setting, field, value)
    setting.updated_by_user_id = current_user.id
    db.commit()
    db.refresh(setting)
    return setting


@router.post("/consents/me", response_model=PrivacyConsentItem)
def create_my_privacy_consent(
    payload: PrivacyConsentCreate,
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    school_id = getattr(current_user, "school_id", None)
    if school_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a school")

    consent = UserPrivacyConsent(
        user_id=current_user.id,
        school_id=school_id,
        consent_type=payload.consent_type.strip(),
        consent_granted=payload.consent_granted,
        consent_version=payload.consent_version.strip(),
        source=payload.source.strip(),
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


@router.get("/consents/me", response_model=list[PrivacyConsentItem])
def list_my_consents(
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(UserPrivacyConsent)
        .filter(UserPrivacyConsent.user_id == current_user.id)
        .order_by(UserPrivacyConsent.created_at.desc())
        .limit(200)
        .all()
    )


@router.post("/requests", response_model=DataRequestItem)
def create_data_request(
    payload: DataRequestCreate,
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    school_id = getattr(current_user, "school_id", None)
    if school_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a school")

    target_user_id = payload.target_user_id or current_user.id
    row = DataRequest(
        school_id=school_id,
        requested_by_user_id=current_user.id,
        target_user_id=target_user_id,
        request_type=payload.request_type,
        scope="user_data",
        status="pending",
        reason=payload.reason,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/requests", response_model=list[DataRequestItem])
def list_data_requests(
    school_id: int | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    request_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    query = db.query(DataRequest)
    actor_school_id = getattr(current_user, "school_id", None)
    is_platform_admin = has_any_role(current_user, ["admin"]) and actor_school_id is None
    privileged = has_any_role(current_user, ["admin", "campus_admin"])

    if privileged:
        if is_platform_admin:
            if school_id is not None:
                query = query.filter(DataRequest.school_id == school_id)
        else:
            if actor_school_id is None:
                raise HTTPException(status_code=403, detail="User is not assigned to a school")
            query = query.filter(DataRequest.school_id == actor_school_id)
    else:
        query = query.filter(DataRequest.requested_by_user_id == current_user.id)

    if status_value:
        query = query.filter(DataRequest.status == status_value)
    if request_type:
        query = query.filter(DataRequest.request_type == request_type)

    return query.order_by(DataRequest.created_at.desc()).limit(limit).all()


def _export_request_payload(db: Session, request_row: DataRequest) -> str:
    user = None
    if request_row.target_user_id is not None:
        user = db.query(User).filter(User.id == request_row.target_user_id).first()

    payload = {
        "request": {
            "id": request_row.id,
            "type": request_row.request_type,
            "status": request_row.status,
            "created_at": request_row.created_at.isoformat(),
        },
        "user": None,
    }
    if user is not None:
        payload["user"] = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "school_id": user.school_id,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    settings = get_settings()
    export_dir = Path(settings.import_storage_dir) / "governance_exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    output_path = export_dir / f"data_request_{request_row.id}.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(output_path)


def _soft_delete_target_user(db: Session, request_row: DataRequest) -> None:
    if request_row.target_user_id is None:
        return
    user = db.query(User).filter(User.id == request_row.target_user_id).first()
    if user is None:
        return
    user.is_active = False
    # Keep anonymized email syntactically valid so response schemas using EmailStr won't fail.
    if "@deleted.example.com" not in user.email:
        user.email = f"deleted_{user.id}_{int(utc_now().timestamp())}@deleted.example.com"


@router.patch("/requests/{request_id}", response_model=DataRequestItem)
def update_data_request_status(
    request_id: int,
    payload: DataRequestStatusUpdate,
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    row = db.query(DataRequest).filter(DataRequest.id == request_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Data request not found")

    actor_school_id = getattr(current_user, "school_id", None)
    is_platform_admin = has_any_role(current_user, ["admin"]) and actor_school_id is None
    if not is_platform_admin and row.school_id != actor_school_id:
        raise HTTPException(status_code=404, detail="Data request not found")

    row.status = payload.status
    row.handled_by_user_id = current_user.id
    if payload.note:
        row.reason = (row.reason or "") + f" | Review note: {payload.note}"

    resolved_at = utc_now()
    if payload.status in {"approved", "completed"}:
        if row.request_type == "export":
            row.output_path = _export_request_payload(db, row)
            row.status = "completed"
            row.resolved_at = resolved_at
        elif row.request_type == "delete":
            _soft_delete_target_user(db, row)
            row.status = "completed"
            row.resolved_at = resolved_at
    elif payload.status == "rejected":
        row.resolved_at = resolved_at

    db.commit()
    db.refresh(row)
    return row


@router.post("/run-retention", response_model=RetentionRunResult)
def run_retention_cleanup(
    payload: RetentionRunRequest,
    school_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    scoped_school_id = _resolve_school_id(current_user, school_id)
    setting = _get_or_create_setting(db, scoped_school_id)

    if not payload.dry_run and not setting.auto_delete_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auto-delete is disabled. Enable it before non-dry-run cleanup.",
        )

    now = utc_now()
    audit_cutoff = now - timedelta(days=setting.audit_log_retention_days)
    import_cutoff = now - timedelta(days=setting.import_file_retention_days)
    notification_cutoff = now - timedelta(days=setting.audit_log_retention_days)

    audit_query = db.query(SchoolAuditLog).filter(
        SchoolAuditLog.school_id == scoped_school_id,
        SchoolAuditLog.created_at < audit_cutoff,
    )
    import_query = db.query(BulkImportJob).filter(
        BulkImportJob.target_school_id == scoped_school_id,
        BulkImportJob.created_at < import_cutoff,
    )
    notification_query = db.query(NotificationLog).filter(
        NotificationLog.school_id == scoped_school_id,
        NotificationLog.created_at < notification_cutoff,
    )

    deleted_audit_logs = audit_query.count()
    deleted_import_logs = import_query.count()
    deleted_notifications = notification_query.count()

    if not payload.dry_run:
        old_import_jobs = import_query.all()
        for job in old_import_jobs:
            for path_value in [job.stored_file_path, job.failed_report_path]:
                if path_value and os.path.exists(path_value):
                    try:
                        os.remove(path_value)
                    except OSError:
                        pass
            db.delete(job)

        notification_query.delete(synchronize_session=False)
        audit_query.delete(synchronize_session=False)

    summary = (
        f"audit_logs={deleted_audit_logs}, import_jobs={deleted_import_logs}, "
        f"notifications={deleted_notifications}, dry_run={payload.dry_run}"
    )
    db.add(
        DataRetentionRunLog(
            school_id=scoped_school_id,
            dry_run=payload.dry_run,
            status="completed",
            summary=summary,
        )
    )
    db.commit()

    return RetentionRunResult(
        school_id=scoped_school_id,
        dry_run=payload.dry_run,
        deleted_audit_logs=deleted_audit_logs,
        deleted_import_logs=deleted_import_logs,
        deleted_notifications=deleted_notifications,
        summary=summary,
    )


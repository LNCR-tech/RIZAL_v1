"""Use: Handles sanctions management API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs sanctions management features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.security import get_current_user_with_roles, has_any_role
from app.models.governance_hierarchy import PermissionCode
from app.models.sanctions import SanctionComplianceStatus
from app.models.user import User
from app.schemas.sanctions import (
    ClearanceDeadlineCreateRequest,
    ClearanceDeadlineResponse,
    PaginatedSanctionRecordsResponse,
    SanctionConfigResponse,
    SanctionConfigUpsertRequest,
    SanctionDelegationResponse,
    SanctionDelegationUpsertRequest,
    SanctionRecordResponse,
    SanctionStudentDetailResponse,
    SanctionsDashboardResponse,
)
from app.services import governance_hierarchy_service, sanctions_service

router = APIRouter(prefix="/sanctions", tags=["sanctions"])


def _ensure_sanctions_permission(
    db: Session,
    *,
    current_user: User,
    permission_code: PermissionCode,
    detail: str,
    allow_governance_role_fallback: bool = False,
    fallback_permission_codes: tuple[PermissionCode, ...] = (),
) -> None:
    if has_any_role(current_user, ["admin", "campus_admin"]):
        return

    governance_unit_types = governance_hierarchy_service.get_user_governance_unit_types(
        db,
        current_user=current_user,
    )
    if allow_governance_role_fallback:
        # Prefer real governance membership fallback so sanctions access follows active SSG/SG/ORG scope ownership.
        if governance_unit_types:
            return
        # Keep legacy role-name fallback for deployments where membership may not be synced yet.
        if has_any_role(
            current_user,
            ["ssg", "sg", "org", "student_council", "student council"],
        ):
            return

    user_permission_codes = governance_hierarchy_service.get_user_governance_permission_codes(
        db,
        current_user=current_user,
    )
    if permission_code in user_permission_codes:
        return

    if any(
        fallback_permission_code in user_permission_codes
        for fallback_permission_code in fallback_permission_codes
    ):
        return

    if governance_unit_types:
        raise HTTPException(status_code=403, detail=detail)

    raise HTTPException(status_code=403, detail="Not authorized to access sanctions management")


@router.get("/events/{event_id}/config", response_model=SanctionConfigResponse)
def get_event_sanction_config(
    event_id: int,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    _ensure_sanctions_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.CONFIGURE_EVENT_SANCTIONS,
        fallback_permission_codes=(PermissionCode.MANAGE_EVENTS,),
        detail=(
            "This governance account has no sanctions configuration features yet. "
            "Campus Admin must assign configure_event_sanctions to the governance member."
        ),
        allow_governance_role_fallback=True,
    )
    return sanctions_service.get_event_sanction_config(
        db,
        current_user=current_user,
        event_id=event_id,
    )


@router.put("/events/{event_id}/config", response_model=SanctionConfigResponse)
def upsert_event_sanction_config(
    event_id: int,
    payload: SanctionConfigUpsertRequest,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    _ensure_sanctions_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.CONFIGURE_EVENT_SANCTIONS,
        fallback_permission_codes=(PermissionCode.MANAGE_EVENTS,),
        detail=(
            "This governance account has no sanctions configuration features yet. "
            "Campus Admin must assign configure_event_sanctions to the governance member."
        ),
        allow_governance_role_fallback=True,
    )
    return sanctions_service.upsert_event_sanction_config(
        db,
        current_user=current_user,
        event_id=event_id,
        payload=payload,
    )


@router.get("/events/{event_id}/students", response_model=PaginatedSanctionRecordsResponse)
def list_event_sanctioned_students(
    event_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=250),
    status_filter: SanctionComplianceStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    _ensure_sanctions_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST,
        detail=(
            "This governance account has no sanctioned-students list access yet. "
            "Campus Admin must assign view_sanctioned_students_list to the governance member."
        ),
        allow_governance_role_fallback=True,
    )
    return sanctions_service.list_event_sanctioned_students(
        db,
        current_user=current_user,
        event_id=event_id,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )


@router.post(
    "/events/{event_id}/students/{user_id}/approve",
    response_model=SanctionRecordResponse,
    status_code=status.HTTP_200_OK,
)
def approve_student_sanction(
    event_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    _ensure_sanctions_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.APPROVE_SANCTION_COMPLIANCE,
        detail=(
            "This governance account has no sanction-approval features yet. "
            "Campus Admin must assign approve_sanction_compliance to the governance member."
        ),
        allow_governance_role_fallback=True,
    )
    return sanctions_service.approve_student_sanction(
        db,
        current_user=current_user,
        event_id=event_id,
        user_id=user_id,
    )


@router.get("/events/{event_id}/delegation", response_model=list[SanctionDelegationResponse])
def get_event_delegation_config(
    event_id: int,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    _ensure_sanctions_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.CONFIGURE_EVENT_SANCTIONS,
        fallback_permission_codes=(PermissionCode.MANAGE_EVENTS,),
        detail=(
            "This governance account has no sanctions configuration features yet. "
            "Campus Admin must assign configure_event_sanctions to the governance member."
        ),
        allow_governance_role_fallback=True,
    )
    return sanctions_service.get_event_delegation_config(
        db,
        current_user=current_user,
        event_id=event_id,
    )


@router.put("/events/{event_id}/delegation", response_model=list[SanctionDelegationResponse])
def set_event_delegation_config(
    event_id: int,
    payload: SanctionDelegationUpsertRequest,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    _ensure_sanctions_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.CONFIGURE_EVENT_SANCTIONS,
        fallback_permission_codes=(PermissionCode.MANAGE_EVENTS,),
        detail=(
            "This governance account has no sanctions configuration features yet. "
            "Campus Admin must assign configure_event_sanctions to the governance member."
        ),
        allow_governance_role_fallback=True,
    )
    return sanctions_service.set_event_delegation_config(
        db,
        current_user=current_user,
        event_id=event_id,
        payload=payload,
    )


@router.get("/dashboard", response_model=SanctionsDashboardResponse)
def get_sanctions_dashboard(
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    _ensure_sanctions_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.VIEW_SANCTIONS_DASHBOARD,
        fallback_permission_codes=(
            PermissionCode.MANAGE_EVENTS,
            PermissionCode.CONFIGURE_EVENT_SANCTIONS,
        ),
        detail=(
            "This governance account has no sanctions dashboard access yet. "
            "Campus Admin must assign view_sanctions_dashboard to the governance member."
        ),
        allow_governance_role_fallback=True,
    )
    return sanctions_service.get_governance_sanctions_dashboard(
        db,
        current_user=current_user,
    )


@router.get("/students/me", response_model=list[SanctionRecordResponse])
def get_my_sanctions(
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    return sanctions_service.get_my_sanctions(
        db,
        current_user=current_user,
    )


@router.get("/students/{user_id}", response_model=SanctionStudentDetailResponse)
def get_student_sanctions_detail(
    user_id: int,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    _ensure_sanctions_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.VIEW_STUDENT_SANCTION_DETAIL,
        detail=(
            "This governance account has no student-sanction detail access yet. "
            "Campus Admin must assign view_student_sanction_detail to the governance member."
        ),
        allow_governance_role_fallback=True,
    )
    return sanctions_service.get_student_sanctions_detail(
        db,
        current_user=current_user,
        user_id=user_id,
    )


@router.post("/clearance-deadline", response_model=ClearanceDeadlineResponse)
def create_clearance_deadline(
    payload: ClearanceDeadlineCreateRequest,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    _ensure_sanctions_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.CONFIGURE_EVENT_SANCTIONS,
        detail=(
            "This governance account has no sanctions configuration features yet. "
            "Campus Admin must assign configure_event_sanctions to the governance member."
        ),
        allow_governance_role_fallback=True,
    )
    return sanctions_service.create_clearance_deadline(
        db,
        current_user=current_user,
        payload=payload,
    )


@router.get("/clearance-deadline", response_model=ClearanceDeadlineResponse | None)
def get_active_clearance_deadline(
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    return sanctions_service.get_active_clearance_deadline(
        db,
        current_user=current_user,
    )


@router.get("/events/{event_id}/export")
def export_event_sanctions_excel(
    event_id: int,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    _ensure_sanctions_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.EXPORT_SANCTIONED_STUDENTS,
        detail=(
            "This governance account has no sanctions export access yet. "
            "Campus Admin must assign export_sanctioned_students to the governance member."
        ),
        allow_governance_role_fallback=True,
    )
    file_bytes, filename = sanctions_service.export_event_sanctions_excel(
        db,
        current_user=current_user,
        event_id=event_id,
    )
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

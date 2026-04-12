"""Use: Handles governance unit hierarchy management API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs governance unit hierarchy management features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.security import (
    get_current_admin_or_campus_admin,
    get_current_user_with_roles,
    has_any_role,
)
from app.models.governance_hierarchy import GovernanceAnnouncementStatus, GovernanceUnitType
from app.reports.system import router as system_reports_router
from app.models.user import User
from app.schemas.governance_hierarchy import (
    GovernanceAccessResponse,
    GovernanceAccessibleStudentResponse,
    GovernanceAnnouncementCreate,
    GovernanceDashboardOverviewResponse,
    GovernanceAnnouncementMonitorResponse,
    GovernanceAnnouncementResponse,
    GovernanceAnnouncementUpdate,
    GovernanceEventDefaultsResponse,
    GovernanceEventDefaultsUpdate,
    GovernanceMemberAssign,
    GovernanceMemberUpdate,
    GovernanceMemberResponse,
    GovernanceSsgSetupResponse,
    GovernanceStudentNoteResponse,
    GovernanceStudentNoteUpdate,
    GovernanceStudentCandidateResponse,
    GovernanceUnitCreate,
    GovernanceUnitDetailResponse,
    GovernanceUnitUpdate,
    GovernanceUnitPermissionAssign,
    GovernanceUnitPermissionResponse,
    GovernanceUnitSummaryResponse,
)
from app.services import governance_hierarchy_service

router = APIRouter(prefix="/api/governance", tags=["governance-hierarchy"])


def get_current_governance_route_user(
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
) -> User:
    if has_any_role(current_user, ["admin", "campus_admin", "student"]):
        return current_user
    if governance_hierarchy_service.get_user_governance_unit_types(
        db,
        current_user=current_user,
    ):
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "A Campus Admin, student, or active governance membership is "
            "required for governance routes"
        ),
    )


@router.get("/access/me", response_model=GovernanceAccessResponse)
def get_my_governance_access(
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.get_current_governance_access(
        db,
        current_user=current_user,
    )


@router.get("/students/search", response_model=list[GovernanceStudentCandidateResponse])
def search_governance_student_candidates(
    search_term: str | None = Query(default=None, alias="q"),
    governance_unit_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.search_governance_student_candidates(
        db,
        current_user=current_user,
        search_term=search_term,
        governance_unit_id=governance_unit_id,
        limit=limit,
    )


@router.get("/students", response_model=list[GovernanceAccessibleStudentResponse])
def list_accessible_governance_students(
    governance_context: GovernanceUnitType | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1, le=250),
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    student_profiles = governance_hierarchy_service.get_accessible_students(
        db,
        current_user=current_user,
        unit_type=governance_context,
        skip=skip,
        limit=limit,
    )
    return [
        GovernanceAccessibleStudentResponse(
            user=student_profile.user,
            student_profile={
                "id": student_profile.id,
                "student_id": student_profile.student_id,
                "department_id": student_profile.department_id,
                "program_id": student_profile.program_id,
                "department_name": getattr(student_profile.department, "name", None),
                "program_name": getattr(student_profile.program, "name", None),
                "year_level": student_profile.year_level,
            },
        )
        for student_profile in student_profiles
    ]


@router.get(
    "/announcements/monitor",
    response_model=list[GovernanceAnnouncementMonitorResponse],
)
def list_school_governance_announcements(
    status: GovernanceAnnouncementStatus | None = Query(default=None),
    unit_type: GovernanceUnitType | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=250),
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.list_school_governance_announcements(
        db,
        current_user=current_user,
        status=status,
        unit_type=unit_type,
        search_term=q,
        limit=limit,
    )


@router.get("/ssg/setup", response_model=GovernanceSsgSetupResponse)
def get_campus_ssg_setup(
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.get_or_create_campus_ssg_setup(
        db,
        current_user=current_user,
    )


@router.post(
    "/units",
    response_model=GovernanceUnitDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_governance_unit(
    payload: GovernanceUnitCreate,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.create_governance_unit(
        db,
        current_user=current_user,
        payload=payload,
    )


@router.patch("/units/{governance_unit_id}", response_model=GovernanceUnitDetailResponse)
def update_governance_unit(
    governance_unit_id: int,
    payload: GovernanceUnitUpdate,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.update_governance_unit(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
        payload=payload,
    )


@router.delete("/units/{governance_unit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_governance_unit(
    governance_unit_id: int,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    governance_hierarchy_service.delete_governance_unit(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/units", response_model=list[GovernanceUnitSummaryResponse])
def list_governance_units(
    unit_type: GovernanceUnitType | None = Query(default=None),
    parent_unit_id: int | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.list_governance_units(
        db,
        current_user=current_user,
        unit_type=unit_type,
        parent_unit_id=parent_unit_id,
        include_inactive=include_inactive,
    )


@router.get("/units/{governance_unit_id}", response_model=GovernanceUnitDetailResponse)
def get_governance_unit_details(
    governance_unit_id: int,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.get_governance_unit_details(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
    )


@router.get(
    "/units/{governance_unit_id}/dashboard-overview",
    response_model=GovernanceDashboardOverviewResponse,
)
def get_governance_dashboard_overview(
    governance_unit_id: int,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return system_reports_router.get_governance_dashboard_overview(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
    )


@router.get(
    "/units/{governance_unit_id}/event-defaults",
    response_model=GovernanceEventDefaultsResponse,
)
def get_governance_unit_event_defaults(
    governance_unit_id: int,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.get_governance_event_defaults(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
    )


@router.put(
    "/units/{governance_unit_id}/event-defaults",
    response_model=GovernanceEventDefaultsResponse,
)
def update_governance_unit_event_defaults(
    governance_unit_id: int,
    payload: GovernanceEventDefaultsUpdate,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.update_governance_event_defaults(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
        payload=payload,
    )


@router.post(
    "/units/{governance_unit_id}/members",
    response_model=GovernanceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_governance_member(
    governance_unit_id: int,
    payload: GovernanceMemberAssign,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.assign_governance_member(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
        payload=payload,
    )


@router.patch("/members/{governance_member_id}", response_model=GovernanceMemberResponse)
def update_governance_member(
    governance_member_id: int,
    payload: GovernanceMemberUpdate,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.update_governance_member(
        db,
        current_user=current_user,
        governance_member_id=governance_member_id,
        payload=payload,
    )


@router.delete("/members/{governance_member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_governance_member(
    governance_member_id: int,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    governance_hierarchy_service.delete_governance_member(
        db,
        current_user=current_user,
        governance_member_id=governance_member_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/units/{governance_unit_id}/announcements",
    response_model=list[GovernanceAnnouncementResponse],
)
def list_governance_announcements(
    governance_unit_id: int,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.list_governance_announcements(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
    )


@router.post(
    "/units/{governance_unit_id}/announcements",
    response_model=GovernanceAnnouncementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_governance_announcement(
    governance_unit_id: int,
    payload: GovernanceAnnouncementCreate,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.create_governance_announcement(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
        payload=payload,
    )


@router.patch(
    "/announcements/{announcement_id}",
    response_model=GovernanceAnnouncementResponse,
)
def update_governance_announcement(
    announcement_id: int,
    payload: GovernanceAnnouncementUpdate,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.update_governance_announcement(
        db,
        current_user=current_user,
        announcement_id=announcement_id,
        payload=payload,
    )


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_governance_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    governance_hierarchy_service.delete_governance_announcement(
        db,
        current_user=current_user,
        announcement_id=announcement_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/units/{governance_unit_id}/student-notes/{student_profile_id}",
    response_model=GovernanceStudentNoteResponse,
)
def get_governance_student_note(
    governance_unit_id: int,
    student_profile_id: int,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.get_governance_student_note(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
        student_profile_id=student_profile_id,
    )


@router.put(
    "/units/{governance_unit_id}/student-notes/{student_profile_id}",
    response_model=GovernanceStudentNoteResponse,
)
def upsert_governance_student_note(
    governance_unit_id: int,
    student_profile_id: int,
    payload: GovernanceStudentNoteUpdate,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.upsert_governance_student_note(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
        student_profile_id=student_profile_id,
        payload=payload,
    )


@router.post(
    "/units/{governance_unit_id}/permissions",
    response_model=GovernanceUnitPermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_governance_permission(
    governance_unit_id: int,
    payload: GovernanceUnitPermissionAssign,
    current_user: User = Depends(get_current_governance_route_user),
    db: Session = Depends(get_db),
):
    return governance_hierarchy_service.assign_unit_permission(
        db,
        current_user=current_user,
        governance_unit_id=governance_unit_id,
        payload=payload,
    )

"""Use: Defines request and response data shapes for governance hierarchy API data.
Where to use: Use this in routers and services when validating or returning governance hierarchy API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.governance_hierarchy import (
    GovernanceAnnouncementStatus,
    GovernanceUnitType,
    PermissionCode,
)


class GovernanceUserSummary(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    school_id: Optional[int] = None
    is_active: bool
    student_profile: Optional["GovernanceStudentProfileSummary"] = None
    model_config = ConfigDict(from_attributes=True)


class GovernanceStudentProfileSummary(BaseModel):
    id: int
    student_id: Optional[str] = None
    department_id: Optional[int] = None
    program_id: Optional[int] = None
    department_name: Optional[str] = None
    program_name: Optional[str] = None
    year_level: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class GovernancePermissionResponse(BaseModel):
    id: int
    permission_code: PermissionCode
    permission_name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class GovernanceUnitPermissionAssign(BaseModel):
    permission_code: PermissionCode


class GovernanceUnitPermissionResponse(BaseModel):
    id: int
    governance_unit_id: int
    permission_id: int
    granted_by_user_id: Optional[int] = None
    created_at: datetime
    permission: GovernancePermissionResponse
    model_config = ConfigDict(from_attributes=True)


class GovernanceMemberAssign(BaseModel):
    user_id: int
    position_title: Optional[str] = Field(default=None, max_length=100)
    permission_codes: list[PermissionCode] = Field(default_factory=list)


class GovernanceMemberUpdate(BaseModel):
    user_id: Optional[int] = None
    position_title: Optional[str] = Field(default=None, max_length=100)
    permission_codes: list[PermissionCode] = Field(default_factory=list)


class GovernanceMemberResponse(BaseModel):
    id: int
    governance_unit_id: int
    user_id: int
    position_title: Optional[str] = None
    assigned_by_user_id: Optional[int] = None
    assigned_at: datetime
    is_active: bool
    user: GovernanceUserSummary
    member_permissions: list["GovernanceMemberPermissionResponse"] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class GovernanceUnitCreate(BaseModel):
    unit_code: str = Field(..., min_length=2, max_length=50)
    unit_name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    unit_type: GovernanceUnitType
    parent_unit_id: Optional[int] = None
    department_id: Optional[int] = None
    program_id: Optional[int] = None


class GovernanceUnitUpdate(BaseModel):
    unit_code: Optional[str] = Field(default=None, min_length=2, max_length=50)
    unit_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)


class GovernanceUnitBaseResponse(BaseModel):
    id: int
    unit_code: str
    unit_name: str
    description: Optional[str] = None
    unit_type: GovernanceUnitType
    parent_unit_id: Optional[int] = None
    school_id: int
    department_id: Optional[int] = None
    program_id: Optional[int] = None
    created_by_user_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GovernanceUnitSummaryResponse(GovernanceUnitBaseResponse):
    member_count: int = 0


class GovernanceUnitDetailResponse(GovernanceUnitBaseResponse):
    members: list[GovernanceMemberResponse] = Field(default_factory=list)
    unit_permissions: list[GovernanceUnitPermissionResponse] = Field(default_factory=list)


class GovernanceSsgSetupResponse(BaseModel):
    unit: GovernanceUnitDetailResponse
    total_imported_students: int


class GovernanceAccessUnitResponse(BaseModel):
    governance_unit_id: int
    unit_code: str
    unit_name: str
    unit_type: GovernanceUnitType
    permission_codes: list[PermissionCode] = Field(default_factory=list)


class GovernanceAccessResponse(BaseModel):
    user_id: int
    school_id: int
    permission_codes: list[PermissionCode] = Field(default_factory=list)
    units: list[GovernanceAccessUnitResponse] = Field(default_factory=list)


class GovernanceMemberPermissionResponse(BaseModel):
    id: int
    permission_id: int
    granted_by_user_id: Optional[int] = None
    created_at: datetime
    permission: GovernancePermissionResponse
    model_config = ConfigDict(from_attributes=True)


class GovernanceStudentCandidateResponse(BaseModel):
    user: GovernanceUserSummary
    student_profile: GovernanceStudentProfileSummary
    is_current_governance_member: bool = False

    model_config = ConfigDict(from_attributes=True)


class GovernanceAccessibleStudentResponse(BaseModel):
    user: GovernanceUserSummary
    student_profile: GovernanceStudentProfileSummary
    model_config = ConfigDict(from_attributes=True)


class GovernanceDashboardAnnouncementSummaryResponse(BaseModel):
    id: int
    title: str
    status: GovernanceAnnouncementStatus
    author_name: Optional[str] = None
    updated_at: datetime


class GovernanceDashboardChildUnitSummaryResponse(BaseModel):
    id: int
    unit_code: str
    unit_name: str
    description: Optional[str] = None
    unit_type: GovernanceUnitType
    member_count: int = 0


class GovernanceDashboardOverviewResponse(BaseModel):
    governance_unit_id: int
    unit_type: GovernanceUnitType
    published_announcement_count: int = 0
    total_students: int = 0
    recent_announcements: list[GovernanceDashboardAnnouncementSummaryResponse] = Field(default_factory=list)
    child_units: list[GovernanceDashboardChildUnitSummaryResponse] = Field(default_factory=list)


class GovernanceEventDefaultsResponse(BaseModel):
    governance_unit_id: int
    school_id: int
    unit_type: GovernanceUnitType
    inherits_school_defaults: bool
    override_early_check_in_minutes: Optional[int] = None
    override_late_threshold_minutes: Optional[int] = None
    override_sign_out_grace_minutes: Optional[int] = None
    effective_early_check_in_minutes: int
    effective_late_threshold_minutes: int
    effective_sign_out_grace_minutes: int


class GovernanceEventDefaultsUpdate(BaseModel):
    early_check_in_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    late_threshold_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    sign_out_grace_minutes: Optional[int] = Field(default=None, ge=0, le=1440)


class GovernanceAnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1, max_length=5000)
    status: GovernanceAnnouncementStatus = GovernanceAnnouncementStatus.DRAFT


class GovernanceAnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, min_length=1, max_length=5000)
    status: Optional[GovernanceAnnouncementStatus] = None


class GovernanceAnnouncementResponse(BaseModel):
    id: int
    governance_unit_id: int
    school_id: int
    title: str
    body: str
    status: GovernanceAnnouncementStatus
    created_by_user_id: Optional[int] = None
    updated_by_user_id: Optional[int] = None
    author_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GovernanceAnnouncementMonitorResponse(GovernanceAnnouncementResponse):
    governance_unit_code: str
    governance_unit_name: str
    governance_unit_type: GovernanceUnitType
    governance_unit_description: Optional[str] = None


class GovernanceStudentNoteUpdate(BaseModel):
    tags: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=5000)


class GovernanceStudentNoteResponse(BaseModel):
    id: int
    governance_unit_id: int
    student_profile_id: int
    school_id: int
    tags: list[str] = Field(default_factory=list)
    notes: str = ""
    created_by_user_id: Optional[int] = None
    updated_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


GovernanceUserSummary.model_rebuild()
GovernanceMemberResponse.model_rebuild()

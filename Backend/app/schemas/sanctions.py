"""Use: Defines request and response data shapes for sanctions API data.
Where to use: Use this in routers and services when validating or returning sanctions API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.governance_hierarchy import GovernanceUnitType
from app.models.sanctions import (
    ClearanceDeadlineStatus,
    SanctionComplianceStatus,
    SanctionDelegationScopeType,
    SanctionItemStatus,
)


class SanctionConfigItemInput(BaseModel):
    item_code: str | None = Field(default=None, min_length=1, max_length=64)
    item_name: str = Field(..., min_length=1, max_length=255)
    item_description: str | None = Field(default=None, max_length=2000)
    metadata_json: dict[str, Any] | None = None


class SanctionConfigUpsertRequest(BaseModel):
    sanctions_enabled: bool
    items: list[SanctionConfigItemInput] = Field(default_factory=list)


class SanctionConfigResponse(BaseModel):
    event_id: int
    sanctions_enabled: bool
    items: list[SanctionConfigItemInput] = Field(default_factory=list)
    created_by_user_id: int | None = None
    updated_by_user_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SanctionStudentSummary(BaseModel):
    user_id: int
    student_profile_id: int
    student_id: str | None = None
    email: str
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    program_id: int | None = None
    program_name: str | None = None
    year_level: int | None = None


class SanctionItemResponse(BaseModel):
    id: int
    item_code: str | None = None
    item_name: str
    item_description: str | None = None
    status: SanctionItemStatus
    complied_at: datetime | None = None
    compliance_notes: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SanctionRecordResponse(BaseModel):
    id: int
    event_id: int
    status: SanctionComplianceStatus
    notes: str | None = None
    complied_at: datetime | None = None
    assigned_by_user_id: int | None = None
    delegated_governance_unit_id: int | None = None
    created_at: datetime
    updated_at: datetime
    student: SanctionStudentSummary
    items: list[SanctionItemResponse] = Field(default_factory=list)


class PaginatedSanctionRecordsResponse(BaseModel):
    total: int
    items: list[SanctionRecordResponse] = Field(default_factory=list)
    skip: int
    limit: int


class SanctionDelegationInput(BaseModel):
    delegated_to_governance_unit_id: int
    scope_type: SanctionDelegationScopeType = SanctionDelegationScopeType.UNIT
    scope_json: dict[str, Any] | None = None
    is_active: bool = True


class SanctionDelegationUpsertRequest(BaseModel):
    delegations: list[SanctionDelegationInput] = Field(default_factory=list)


class SanctionDelegationResponse(BaseModel):
    id: int
    event_id: int
    delegated_by_user_id: int | None = None
    delegated_to_governance_unit_id: int
    delegated_to_unit_code: str | None = None
    delegated_to_unit_name: str | None = None
    delegated_to_unit_type: GovernanceUnitType | None = None
    scope_type: SanctionDelegationScopeType
    scope_json: dict[str, Any] | None = None
    is_active: bool
    revoked_at: datetime | None = None
    revoked_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class SanctionDashboardEventSummary(BaseModel):
    event_id: int
    event_name: str
    owner_level: GovernanceUnitType
    participant_count: int
    absent_count: int
    pending_sanctions: int
    complied_sanctions: int
    absence_rate_percent: float


class SanctionsDashboardResponse(BaseModel):
    total_events: int
    total_participants: int
    total_absent: int
    total_pending_sanctions: int
    total_complied_sanctions: int
    overall_absence_rate_percent: float
    events: list[SanctionDashboardEventSummary] = Field(default_factory=list)


class SanctionStudentDetailResponse(BaseModel):
    user_id: int
    sanctions: list[SanctionRecordResponse] = Field(default_factory=list)


class ClearanceDeadlineCreateRequest(BaseModel):
    event_id: int
    deadline_at: datetime
    message: str | None = Field(default=None, max_length=2000)
    target_governance_unit_id: int | None = None


class ClearanceDeadlineResponse(BaseModel):
    id: int
    school_id: int
    event_id: int
    declared_by_user_id: int | None = None
    target_governance_unit_id: int | None = None
    deadline_at: datetime
    status: ClearanceDeadlineStatus
    warning_email_sent_at: datetime | None = None
    warning_popup_sent_at: datetime | None = None
    message: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SanctionComplianceHistoryResponse(BaseModel):
    id: int
    event_id: int | None = None
    sanction_record_id: int | None = None
    sanction_item_id: int | None = None
    student_profile_id: int | None = None
    complied_on: date
    school_year: str
    semester: str
    complied_by_user_id: int | None = None
    notes: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

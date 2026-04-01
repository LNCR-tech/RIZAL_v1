"""Use: Defines request and response data shapes for school settings API data.
Where to use: Use this in routers and services when validating or returning school settings API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


HEX_COLOR_PATTERN = r"^#(?:[0-9a-fA-F]{6})$"


class SchoolSettingsResponse(BaseModel):
    school_id: int
    school_name: str
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    accent_color: str
    event_default_early_check_in_minutes: int
    event_default_late_threshold_minutes: int
    event_default_sign_out_grace_minutes: int

    model_config = ConfigDict(from_attributes=True)


class SchoolSettingsUpdate(BaseModel):
    school_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    logo_url: Optional[str] = Field(default=None, max_length=1000)
    primary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)
    secondary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)
    accent_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)
    event_default_early_check_in_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    event_default_late_threshold_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    event_default_sign_out_grace_minutes: Optional[int] = Field(default=None, ge=0, le=1440)


class SchoolAuditLogResponse(BaseModel):
    id: int
    action: str
    status: str
    details: Optional[str] = None
    created_at: datetime
    actor_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserImportRowResult(BaseModel):
    row_number: int
    email: Optional[str] = None
    status: str
    errors: List[str] = Field(default_factory=list)
    user_id: Optional[int] = None


class UserImportSummary(BaseModel):
    filename: str
    total_rows: int
    created_count: int
    failed_count: int
    results: List[UserImportRowResult] = Field(default_factory=list)

"""Use: Defines request and response data shapes for school and branding API data.
Where to use: Use this in routers and services when validating or returning school and branding API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

HEX_COLOR_PATTERN = r"^#(?:[0-9a-fA-F]{6})$"


def _as_utc_datetime(value):
    """Normalize naive datetimes as UTC so API responses include an explicit offset."""
    if not isinstance(value, datetime):
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class SchoolBrandingResponse(BaseModel):
    school_id: int
    school_name: str
    school_code: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: Optional[str] = None
    event_default_early_check_in_minutes: int
    event_default_late_threshold_minutes: int
    event_default_sign_out_grace_minutes: int
    subscription_status: str
    active_status: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def normalize_branding_timestamps(cls, value):
        return _as_utc_datetime(value)

    model_config = ConfigDict(from_attributes=True)


class SchoolCreateForm(BaseModel):
    school_name: str = Field(min_length=2, max_length=255)
    primary_color: str = Field(pattern=HEX_COLOR_PATTERN)
    secondary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)
    school_code: Optional[str] = Field(default=None, min_length=2, max_length=50)


class SchoolUpdateForm(BaseModel):
    school_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    primary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)
    secondary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)
    school_code: Optional[str] = Field(default=None, min_length=2, max_length=50)
    event_default_early_check_in_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    event_default_late_threshold_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    event_default_sign_out_grace_minutes: Optional[int] = Field(default=None, ge=0, le=1440)


class AdminSchoolItCreateForm(BaseModel):
    school_name: str = Field(min_length=2, max_length=255)
    primary_color: str = Field(pattern=HEX_COLOR_PATTERN)
    secondary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)
    school_code: Optional[str] = Field(default=None, min_length=2, max_length=50)

    school_it_email: str = Field(min_length=5, max_length=255)
    school_it_first_name: str = Field(min_length=1, max_length=100)
    school_it_middle_name: Optional[str] = Field(default=None, max_length=100)
    school_it_last_name: str = Field(min_length=1, max_length=100)
    school_it_password: Optional[str] = Field(default=None, min_length=8, max_length=255)


class AdminSchoolItCreateResponse(BaseModel):
    school: SchoolBrandingResponse
    school_it_user_id: int
    school_it_email: str
    generated_temporary_password: Optional[str] = None


class SchoolStatusUpdateForm(BaseModel):
    active_status: Optional[bool] = None
    subscription_status: Optional[str] = Field(default=None, min_length=2, max_length=30)


class SchoolSummaryResponse(BaseModel):
    school_id: int
    school_name: str
    school_code: Optional[str] = None
    subscription_status: str
    active_status: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def normalize_summary_timestamps(cls, value):
        return _as_utc_datetime(value)


class SchoolITAccountResponse(BaseModel):
    user_id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    is_active: bool

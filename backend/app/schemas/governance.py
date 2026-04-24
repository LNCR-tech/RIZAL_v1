"""Use: Defines request and response data shapes for governance settings and member API data.
Where to use: Use this in routers and services when validating or returning governance settings and member API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _as_utc_datetime(value):
    """Normalize naive datetimes as UTC so API responses include an explicit offset."""
    if not isinstance(value, datetime):
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class DataGovernanceSettingResponse(BaseModel):
    school_id: int
    attendance_retention_days: int
    audit_log_retention_days: int
    import_file_retention_days: int
    auto_delete_enabled: bool
    updated_at: datetime

    @field_validator("updated_at", mode="before")
    @classmethod
    def normalize_updated_at_timezone(cls, value):
        return _as_utc_datetime(value)

    model_config = ConfigDict(from_attributes=True)


class DataGovernanceSettingUpdate(BaseModel):
    attendance_retention_days: Optional[int] = Field(default=None, ge=30, le=3650)
    audit_log_retention_days: Optional[int] = Field(default=None, ge=90, le=7300)
    import_file_retention_days: Optional[int] = Field(default=None, ge=7, le=3650)
    auto_delete_enabled: Optional[bool] = None


class PrivacyConsentCreate(BaseModel):
    consent_type: str = Field(min_length=2, max_length=50)
    consent_granted: bool = True
    consent_version: str = Field(default="v1", min_length=1, max_length=20)
    source: str = Field(default="web", min_length=2, max_length=50)


class PrivacyConsentItem(BaseModel):
    id: int
    user_id: int
    school_id: int
    consent_type: str
    consent_granted: bool
    consent_version: str
    source: str
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def normalize_created_at_timezone(cls, value):
        return _as_utc_datetime(value)

    model_config = ConfigDict(from_attributes=True)


class DataRequestCreate(BaseModel):
    request_type: str = Field(pattern="^(export|delete)$")
    reason: Optional[str] = Field(default=None, max_length=2000)
    target_user_id: Optional[int] = None
    details_json: Optional[dict[str, Any]] = None


class DataRequestStatusUpdate(BaseModel):
    status: str = Field(pattern="^(approved|rejected|completed)$")
    note: Optional[str] = Field(default=None, max_length=2000)


class DataRequestItem(BaseModel):
    id: int
    school_id: int
    requested_by_user_id: Optional[int] = None
    target_user_id: Optional[int] = None
    request_type: str
    scope: str
    status: str
    reason: Optional[str] = None
    details_json: Optional[dict[str, Any]] = None
    output_path: Optional[str] = None
    handled_by_user_id: Optional[int] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    @field_validator("created_at", "resolved_at", mode="before")
    @classmethod
    def normalize_request_timestamps(cls, value):
        return _as_utc_datetime(value)

    model_config = ConfigDict(from_attributes=True)


class RetentionRunRequest(BaseModel):
    dry_run: bool = True


class RetentionRunResult(BaseModel):
    school_id: int
    dry_run: bool
    deleted_audit_logs: int
    deleted_import_logs: int
    deleted_notifications: int
    summary: str

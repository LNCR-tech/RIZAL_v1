"""Use: Defines request and response data shapes for security center API data.
Where to use: Use this in routers and services when validating or returning security center API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


def _as_utc_datetime(value):
    """Normalize naive datetimes as UTC so API responses include an explicit offset."""
    if not isinstance(value, datetime):
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class UserSessionItem(BaseModel):
    id: str
    token_jti: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    last_seen_at: datetime
    revoked_at: Optional[datetime] = None
    expires_at: datetime
    is_current: bool = False

    @field_validator("created_at", "last_seen_at", "revoked_at", "expires_at", mode="before")
    @classmethod
    def normalize_session_timestamps(cls, value):
        return _as_utc_datetime(value)

    model_config = ConfigDict(from_attributes=True)


class RevokeSessionResponse(BaseModel):
    session_id: str
    revoked: bool


class RevokeOtherSessionsResponse(BaseModel):
    revoked_count: int


class DeleteFaceReferenceResponse(BaseModel):
    user_id: int
    face_reference_enrolled: bool


class LoginHistoryItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    school_id: Optional[int] = None
    email_attempted: str
    success: bool
    auth_method: str
    failure_reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def normalize_created_at_timezone(cls, value):
        return _as_utc_datetime(value)

    model_config = ConfigDict(from_attributes=True)

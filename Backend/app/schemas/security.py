from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MfaChallengeVerifyRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    challenge_id: str = Field(min_length=8, max_length=64)
    code: str = Field(min_length=4, max_length=12)


class MfaStatusResponse(BaseModel):
    user_id: int
    mfa_enabled: bool
    trusted_device_days: int
    updated_at: datetime


class MfaStatusUpdate(BaseModel):
    mfa_enabled: bool
    trusted_device_days: Optional[int] = Field(default=None, ge=1, le=60)


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

    class Config:
        from_attributes = True


class RevokeSessionResponse(BaseModel):
    session_id: str
    revoked: bool


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

    class Config:
        from_attributes = True

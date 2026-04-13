"""Use: Defines request and response data shapes for security center API data.
Where to use: Use this in routers and services when validating or returning security center API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)

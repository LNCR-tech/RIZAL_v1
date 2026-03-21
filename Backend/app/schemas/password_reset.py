"""Use: Defines request and response data shapes for password reset API data.
Where to use: Use this in routers and services when validating or returning password reset API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class ForgotPasswordRequestCreate(BaseModel):
    email: EmailStr


class ForgotPasswordRequestResponse(BaseModel):
    message: str


class PasswordResetRequestItem(BaseModel):
    id: int
    user_id: int
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    roles: list[str]
    status: str
    requested_at: datetime


class PasswordResetApprovalResponse(BaseModel):
    id: int
    user_id: int
    status: str
    resolved_at: datetime
    message: str

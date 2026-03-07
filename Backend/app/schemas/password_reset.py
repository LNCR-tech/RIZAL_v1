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

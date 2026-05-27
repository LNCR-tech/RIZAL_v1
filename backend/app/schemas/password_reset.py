"""Use: Defines request and response data shapes for password reset API data.
Where to use: Use this in routers and services when validating or returning password reset API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from pydantic import BaseModel, EmailStr


class ForgotPasswordRequestCreate(BaseModel):
    email: EmailStr


class ForgotPasswordRequestResponse(BaseModel):
    message: str


class PasswordResetVerifyRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class PasswordResetCodeResponse(BaseModel):
    message: str

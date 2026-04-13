"""Use: Defines request and response data shapes for authentication API data.
Where to use: Use this in routers and services when validating or returning authentication API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    email: Optional[str] = None
    roles: Optional[List[str]] = None
    user_id: Optional[int] = None
    is_admin: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    school_code: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    must_change_password: Optional[bool] = None
    change_password_endpoint: Optional[str] = None
    password_change_recommended: Optional[bool] = None
    session_id: Optional[str] = None
    face_verification_required: Optional[bool] = None
    face_reference_enrolled: Optional[bool] = None
    face_verification_pending: Optional[bool] = None
    

class TokenData(BaseModel):
    email: Optional[str] = None
    roles: Optional[List[str]] = None  # Added roles for better access control
    school_id: Optional[int] = None
    must_change_password: Optional[bool] = None
    jti: Optional[str] = None
    face_pending: Optional[bool] = None

class LoginRequest(BaseModel):
    email: EmailStr  # More strict validation
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class RoleEnum(str, Enum):
    admin = "admin"
    campus_admin = "campus_admin"
    student = "student"
    
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    roles: List[RoleEnum]  # Now includes all possible roles

# Reorder your classes in app/schemas/user.py:

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from enum import Enum
from datetime import datetime
from app.schemas.role import Role
from app.models.user import StudentProfile
from app.models.attendance import Attendance
from app.schemas.attendance import Attendance  # Now safe to import


class RoleEnum(str, Enum):
    student = "student"
    campus_admin = "campus_admin"
    admin = "admin"

# Base classes first
class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    middle_name: Optional[str] = None
    last_name: str

class StudentProfileBase(BaseModel):
    student_id: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9-]+$",
        example="CS-2023-001",
        description="Official student ID following format: [DepartmentCode]-[Year]-[SequenceNumber]"
    )
    department_id: Optional[int] = Field(
        None,
        description="ID of the department the student belongs to"
    )
    program_id: Optional[int] = Field(
        None,
        description="ID of the academic program the student is enrolled in"
    )
    year_level: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Year level must be between 1 and 5"
    )
# To this (correct):
class StudentProfileWithAttendances(StudentProfileBase):
    id: int
    attendances: List["Attendance"] = []  # String literal
    
    class Config:
        from_attributes = True

# Create and update schemas
class UserCreate(UserBase):
    password: Optional[str] = None
    roles: List[RoleEnum]

class UserUpdate(BaseModel):
    """Schema for partially updating user information"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

class StudentProfileCreate(StudentProfileBase):
    user_id: int = Field(
        ...,
        description="The ID of the user to be assigned as a student"
    )

    @validator('student_id')
    def validate_student_id_format(cls, v):
        """Additional validation for student ID format"""
        if not any(char.isalpha() for char in v):
            raise ValueError("Student ID must contain at least one letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Student ID must contain at least one number")
        return v.upper()

# For password reset/change
class PasswordUpdate(BaseModel):
    password: str = Field(
        ..., 
        min_length=8,
        description="New password"
    )
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password has minimum strength requirements"""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

# For updating user roles
class UserRoleUpdate(BaseModel):
    roles: List[RoleEnum] = Field(
        ...,
        description="List of roles to assign to the user"
    )

# For bulk operations (optional)
class UserIdList(BaseModel):
    """Schema for bulk operations on users"""
    user_ids: List[int] = Field(
        ...,
        min_items=1,
        description="List of user IDs for bulk operations"
    )

# For filtering users (optional)
class UserFilter(BaseModel):
    """Optional schema for advanced user filtering"""
    department_id: Optional[int] = None
    program_id: Optional[int] = None
    year_level: Optional[int] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None

class UserRoleResponse(BaseModel):
    role: Role
    
    class Config:
        from_attributes = True

class StudentProfile(StudentProfileBase):
    id: int
    is_face_registered: bool = False
    registration_complete: bool = False
    attendances: List[Attendance] = []
    
    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    school_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    roles: List[UserRoleResponse] = []
    
    class Config:
        from_attributes = True


class UserCreateResponse(User):
    generated_temporary_password: Optional[str] = None


class UserWithRelations(User):
    student_profile: Optional[StudentProfile] = None

# Resolve forward references
User.update_forward_refs()
StudentProfileWithAttendances.update_forward_refs()

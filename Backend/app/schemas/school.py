from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

HEX_COLOR_PATTERN = r"^#(?:[0-9a-fA-F]{6})$"


class SchoolBrandingResponse(BaseModel):
    school_id: int
    school_name: str
    school_code: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: Optional[str] = None
    subscription_status: str
    active_status: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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


class SchoolITAccountResponse(BaseModel):
    user_id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    is_active: bool

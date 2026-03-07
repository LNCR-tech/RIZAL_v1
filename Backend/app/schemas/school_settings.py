from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


HEX_COLOR_PATTERN = r"^#(?:[0-9a-fA-F]{6})$"


class SchoolSettingsResponse(BaseModel):
    school_id: int
    school_name: str
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    accent_color: str

    class Config:
        from_attributes = True


class SchoolSettingsUpdate(BaseModel):
    school_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    logo_url: Optional[str] = Field(default=None, max_length=1000)
    primary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)
    secondary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)
    accent_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)


class SchoolAuditLogResponse(BaseModel):
    id: int
    action: str
    status: str
    details: Optional[str] = None
    created_at: datetime
    actor_user_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserImportRowResult(BaseModel):
    row_number: int
    email: Optional[str] = None
    status: str
    errors: List[str] = Field(default_factory=list)
    user_id: Optional[int] = None


class UserImportSummary(BaseModel):
    filename: str
    total_rows: int
    created_count: int
    failed_count: int
    results: List[UserImportRowResult] = Field(default_factory=list)

"""Use: Defines request and response data shapes for attendance request payloads.
Where to use: Use this in routers and services when validating or returning attendance request payloads.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.attendance import AttendanceStatus, _as_utc_datetime


class ManualAttendanceRequest(BaseModel):
    event_id: int = Field(..., gt=0)
    student_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    student_profile_id: Optional[int] = Field(default=None, gt=0)
    notes: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def require_student_identifier(self):
        if self.student_id is None and self.student_profile_id is None:
            raise ValueError("Either student_id or student_profile_id is required.")
        return self


class BulkAttendanceRequest(BaseModel):
    records: list[ManualAttendanceRequest] = Field(..., min_length=1, max_length=500)


class FaceScanAttendanceRequest(BaseModel):
    event_id: int = Field(..., gt=0)
    student_id: str = Field(..., min_length=1, max_length=100)


class FaceScanTimeoutRequest(FaceScanAttendanceRequest):
    pass


class MarkAbsentNoTimeoutRequest(BaseModel):
    event_id: int = Field(..., gt=0)


class MarkExcusedAttendanceRequest(BaseModel):
    student_ids: list[str] = Field(..., min_length=1, max_length=500)
    reason: str = Field(..., min_length=1, max_length=1000)


class AttendanceActionResponse(BaseModel):
    message: str
    attendance_id: Optional[int] = None
    student_id: Optional[str] = None
    action: Optional[str] = None
    time_in: Optional[datetime] = None
    time_out: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    @field_validator("time_in", "time_out", mode="before")
    @classmethod
    def normalize_action_timestamps(cls, value):
        return _as_utc_datetime(value)


class BulkAttendanceResult(BaseModel):
    student_id: str
    status: str


class BulkAttendanceResponse(BaseModel):
    processed: int = Field(ge=0)
    results: list[BulkAttendanceResult] = Field(default_factory=list)


class MarkExcusedAttendanceResponse(BaseModel):
    message: str


class MarkAbsentNoTimeoutResponse(BaseModel):
    message: str
    event_id: int
    updated_count: int = Field(ge=0)


class EventAttendanceStatusBreakdown(BaseModel):
    count: int = Field(ge=0)
    percentage: float = Field(ge=0, le=100)


class EventAttendanceStatsResponse(BaseModel):
    total: int = Field(ge=0)
    statuses: dict[str, EventAttendanceStatusBreakdown] = Field(default_factory=dict)


class StudentAttendanceFilter(BaseModel):
    event_id: Optional[int] = None
    status: Optional[AttendanceStatus] = None

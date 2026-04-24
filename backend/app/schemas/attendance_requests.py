"""Use: Defines request and response data shapes for attendance request payloads.
Where to use: Use this in routers and services when validating or returning attendance request payloads.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.attendance import AttendanceStatus


class ManualAttendanceRequest(BaseModel):
    event_id: int = Field(..., gt=0)
    student_id: str = Field(..., min_length=1)
    notes: Optional[str] = None


class BulkAttendanceRequest(BaseModel):
    records: list[ManualAttendanceRequest]


class StudentAttendanceFilter(BaseModel):
    event_id: Optional[int] = None
    status: Optional[AttendanceStatus] = None

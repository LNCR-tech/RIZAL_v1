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

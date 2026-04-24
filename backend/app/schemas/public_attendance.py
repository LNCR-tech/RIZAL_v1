"""Use: Defines public login-page attendance kiosk request and response payloads.
Where to use: Use this in the unauthenticated public attendance router and frontend-facing kiosk flows.
Role: Schema layer. It keeps the public attendance API typed and consistent.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.event import EventLocationVerificationResponse
from app.schemas.face_recognition import Base64ImageRequest


class PublicAttendanceNearbyEventsRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: Optional[float] = Field(default=None, gt=0, le=5000)


class PublicAttendanceEventSummary(BaseModel):
    id: int
    school_id: int
    school_name: str
    name: str
    location: str
    start_datetime: datetime
    end_datetime: datetime
    geo_radius_m: float
    distance_m: float
    effective_distance_m: Optional[float] = None
    accuracy_m: Optional[float] = None
    attendance_phase: Literal["sign_in", "sign_out"]
    phase_message: str
    scope_label: str
    departments: list[str] = Field(default_factory=list)
    programs: list[str] = Field(default_factory=list)


class PublicAttendanceNearbyEventsResponse(BaseModel):
    events: list[PublicAttendanceEventSummary] = Field(default_factory=list)
    scan_cooldown_seconds: int


class PublicAttendanceMultiFaceScanRequest(Base64ImageRequest):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: Optional[float] = Field(default=None, gt=0, le=5000)
    threshold: Optional[float] = Field(default=None, gt=0, le=2)
    cooldown_student_ids: list[str] = Field(default_factory=list, max_length=100)


class PublicAttendanceFaceOutcome(BaseModel):
    action: Literal[
        "time_in",
        "time_out",
        "already_signed_in",
        "already_signed_out",
        "rejected",
        "out_of_scope",
        "no_match",
        "liveness_failed",
        "duplicate_face",
        "cooldown_skipped",
    ]
    reason_code: Optional[str] = None
    message: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    attendance_id: Optional[int] = None
    distance: Optional[float] = None
    confidence: Optional[float] = None
    threshold: Optional[float] = None
    liveness: Optional[dict[str, object]] = None
    time_in: Optional[datetime] = None
    time_out: Optional[datetime] = None
    duration_minutes: Optional[int] = None


class PublicAttendanceMultiFaceScanResponse(BaseModel):
    event_id: int
    event_phase: Literal["sign_in", "sign_out"]
    message: str
    scan_cooldown_seconds: int
    geo: Optional[EventLocationVerificationResponse] = None
    outcomes: list[PublicAttendanceFaceOutcome] = Field(default_factory=list)

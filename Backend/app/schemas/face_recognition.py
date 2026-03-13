from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.event import EventLocationVerificationResponse


class Base64ImageRequest(BaseModel):
    image_base64: str = Field(min_length=32)


class FaceRegistrationResponse(BaseModel):
    message: str
    student_id: str
    liveness: dict[str, object]


class FaceVerificationResponse(BaseModel):
    match_found: bool
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    distance: Optional[float] = None
    confidence: Optional[float] = None
    threshold: Optional[float] = None
    liveness: dict[str, object]


class FaceAttendanceScanRequest(Base64ImageRequest):
    event_id: int = Field(gt=0)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    accuracy_m: Optional[float] = Field(default=None, gt=0, le=5000)
    threshold: Optional[float] = Field(default=None, gt=0, le=2)


class FaceAttendanceScanResponse(BaseModel):
    action: str
    student_id: str
    student_name: str
    attendance_id: int
    distance: float
    confidence: float
    threshold: float
    liveness: dict[str, object]
    geo: Optional[EventLocationVerificationResponse] = None
    time_in: Optional[datetime] = None
    time_out: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    message: Optional[str] = None


class SecurityFaceStatusResponse(BaseModel):
    user_id: int
    face_verification_required: bool
    face_reference_enrolled: bool
    provider: str
    updated_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    liveness_enabled: bool
    anti_spoof_ready: bool
    anti_spoof_reason: Optional[str] = None
    live_capture_required: bool


class SecurityFaceReferenceResponse(BaseModel):
    user_id: int
    face_reference_enrolled: bool
    provider: str
    updated_at: datetime
    liveness: dict[str, object]


class SecurityFaceLivenessResponse(BaseModel):
    label: str
    score: float
    reason: Optional[str] = None


class SecurityFaceVerificationRequest(Base64ImageRequest):
    threshold: Optional[float] = Field(default=None, gt=0, le=2)


class SecurityFaceVerificationResponse(BaseModel):
    matched: bool
    distance: float
    confidence: float
    threshold: float
    liveness: dict[str, object]
    verified_at: Optional[datetime] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    session_id: Optional[str] = None
    face_verification_pending: Optional[bool] = None


__all__ = [
    "Base64ImageRequest",
    "FaceAttendanceScanRequest",
    "FaceAttendanceScanResponse",
    "FaceRegistrationResponse",
    "FaceVerificationResponse",
    "SecurityFaceLivenessResponse",
    "SecurityFaceReferenceResponse",
    "SecurityFaceStatusResponse",
    "SecurityFaceVerificationRequest",
    "SecurityFaceVerificationResponse",
]

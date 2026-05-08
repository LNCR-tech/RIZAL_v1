"""Use: Defines request and response data shapes for event API data.
Where to use: Use this in routers and services when validating or returning event API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator
from datetime import datetime
from enum import Enum

from app.core.timezones import PHILIPPINE_TIMEZONE
from app.core.event_defaults import (
    DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES,
    DEFAULT_EVENT_LATE_THRESHOLD_MINUTES,
    DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES,
)
from app.schemas.attendance import Attendance, AttendanceStatus
from app.schemas.department import Department
from app.schemas.event_type import EventTypeSummary
from app.schemas.program import Program

class EventStatus(str, Enum):
    upcoming = "upcoming"
    ongoing = "ongoing"
    completed = "completed"
    cancelled = "cancelled"


class EventTargetScope(str, Enum):
    ALL = "ALL"
    YEAR_LEVEL = "YEAR_LEVEL"
    DEPARTMENT = "DEPARTMENT"
    COURSE = "COURSE"
    DEPARTMENT_YEAR = "DEPARTMENT_YEAR"
    COURSE_YEAR = "COURSE_YEAR"


class EventTimeStatus(str, Enum):
    before_check_in = "before_check_in"
    early_check_in = "early_check_in"
    late_check_in = "late_check_in"
    absent_check_in = "absent_check_in"
    sign_out_pending = "sign_out_pending"
    sign_out_open = "sign_out_open"
    closed = "closed"


class EventTimeStatusInfo(BaseModel):
    event_status: EventTimeStatus
    current_time: datetime
    check_in_opens_at: datetime
    start_time: datetime
    end_time: datetime
    late_threshold_time: datetime
    attendance_override_active: bool
    effective_present_until_at: datetime
    effective_late_until_at: datetime
    sign_out_opens_at: datetime
    normal_sign_out_closes_at: datetime
    effective_sign_out_closes_at: datetime
    timezone_name: str


class EventAttendanceDecisionInfo(BaseModel):
    action: str = "check_in"
    event_status: EventTimeStatus
    attendance_allowed: bool
    attendance_status: Optional[AttendanceStatus] = None
    reason_code: Optional[str] = None
    message: str
    current_time: datetime
    check_in_opens_at: datetime
    start_time: datetime
    end_time: datetime
    late_threshold_time: datetime
    attendance_override_active: bool
    effective_present_until_at: datetime
    effective_late_until_at: datetime
    sign_out_opens_at: datetime
    normal_sign_out_closes_at: datetime
    effective_sign_out_closes_at: datetime
    timezone_name: str


class EventLocationVerificationRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: Optional[float] = Field(default=None, gt=0, le=5000)


class EventStatusUpdateRequest(BaseModel):
    status: EventStatus


class SignOutOpenEarlyRequest(BaseModel):
    use_sign_out_grace_minutes: bool = Field(
        default=True,
        description="If true, close early sign-out using the event's current sign_out_grace_minutes value.",
    )
    close_after_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        le=1440,
        description="Custom number of minutes to keep sign-out open after ending the event early.",
    )

    @model_validator(mode="after")
    def validate_close_after_minutes(self) -> "SignOutOpenEarlyRequest":
        if self.use_sign_out_grace_minutes:
            return self
        if self.close_after_minutes is None:
            raise ValueError(
                "close_after_minutes is required when use_sign_out_grace_minutes is false."
            )
        return self


class EventLocationVerificationResponse(BaseModel):
    ok: bool
    reason: Optional[str] = None
    distance_m: float
    effective_distance_m: Optional[float] = None
    radius_m: float
    accuracy_m: Optional[float] = None
    time_status: Optional[EventTimeStatusInfo] = None
    attendance_decision: Optional[EventAttendanceDecisionInfo] = None


class EventTargetBase(BaseModel):
    scope_type: EventTargetScope
    year_level: Optional[int] = Field(None, ge=1, le=5)
    department_id: Optional[int] = None
    course_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_scope_combinations(self) -> "EventTargetBase":
        scope = self.scope_type
        if scope == EventTargetScope.ALL:
            if any([self.year_level, self.department_id, self.course_id]):
                raise ValueError("ALL scope cannot have year_level, department_id, or course_id")
        elif scope == EventTargetScope.YEAR_LEVEL:
            if self.year_level is None:
                raise ValueError("YEAR_LEVEL scope requires year_level")
            if any([self.department_id, self.course_id]):
                raise ValueError("YEAR_LEVEL scope cannot have department_id or course_id")
        elif scope == EventTargetScope.DEPARTMENT:
            if self.department_id is None:
                raise ValueError("DEPARTMENT scope requires department_id")
            if any([self.year_level, self.course_id]):
                raise ValueError("DEPARTMENT scope cannot have year_level or course_id")
        elif scope == EventTargetScope.COURSE:
            if self.course_id is None:
                raise ValueError("COURSE scope requires course_id")
            if any([self.year_level, self.department_id]):
                raise ValueError("COURSE scope cannot have year_level or department_id")
        elif scope == EventTargetScope.DEPARTMENT_YEAR:
            if not all([self.department_id, self.year_level]):
                raise ValueError("DEPARTMENT_YEAR scope requires both department_id and year_level")
            if self.course_id:
                raise ValueError("DEPARTMENT_YEAR scope cannot have course_id")
        elif scope == EventTargetScope.COURSE_YEAR:
            if not all([self.course_id, self.year_level]):
                raise ValueError("COURSE_YEAR scope requires both course_id and year_level")
            if self.department_id:
                raise ValueError("COURSE_YEAR scope cannot have department_id")
        return self


class EventTargetCreate(EventTargetBase):
    pass


class EventTarget(EventTargetBase):
    id: int
    event_id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)

class EventBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None)
    venue: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    banner_url: Optional[str] = Field(default=None)
    geo_latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    geo_longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    geo_radius_m: Optional[float] = Field(default=None, gt=0, le=5000)
    geo_required: bool = False
    geo_max_accuracy_m: Optional[float] = Field(default=None, gt=0, le=1000)
    early_check_in_minutes: int = Field(
        default=DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES,
        ge=0,
        le=1440,
    )
    late_threshold_minutes: int = Field(
        default=DEFAULT_EVENT_LATE_THRESHOLD_MINUTES,
        ge=0,
        le=1440,
    )
    sign_out_grace_minutes: int = Field(
        default=DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES,
        ge=0,
        le=1440,
    )
    sign_out_open_delay_minutes: int = Field(
        default=0,
        ge=0,
        le=1440,
    )
    start_datetime: datetime
    end_datetime: datetime
    status: EventStatus = EventStatus.upcoming
    event_type_id: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_sign_out_window(self) -> "EventBase":
        if self.sign_out_open_delay_minutes > self.sign_out_grace_minutes:
            raise ValueError(
                "sign_out_open_delay_minutes cannot be greater than sign_out_grace_minutes."
            )
        return self

class EventCreate(EventBase):
    department_ids: List[int] = Field(default_factory=list)
    program_ids: List[int] = Field(default_factory=list)
    event_targets: List[EventTargetCreate] = Field(default_factory=list)

    @field_validator("start_datetime", "end_datetime", mode="after")
    @classmethod
    def normalize_event_datetime_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=PHILIPPINE_TIMEZONE)
        return value.astimezone(PHILIPPINE_TIMEZONE)

class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    venue: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)
    banner_url: Optional[str] = Field(None)
    geo_latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    geo_longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    geo_radius_m: Optional[float] = Field(default=None, gt=0, le=5000)
    geo_required: Optional[bool] = None
    geo_max_accuracy_m: Optional[float] = Field(default=None, gt=0, le=1000)
    early_check_in_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    late_threshold_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    sign_out_grace_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    sign_out_open_delay_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    status: Optional[EventStatus] = None
    department_ids: Optional[List[int]] = None
    program_ids: Optional[List[int]] = None
    event_targets: Optional[List[EventTargetCreate]] = None

    @field_validator("start_datetime", "end_datetime", mode="after")
    @classmethod
    def normalize_optional_event_datetime_timezone(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=PHILIPPINE_TIMEZONE)
        return value.astimezone(PHILIPPINE_TIMEZONE)

    @model_validator(mode="after")
    def validate_sign_out_window(self) -> "EventUpdate":
        if (
            self.sign_out_open_delay_minutes is not None
            and self.sign_out_grace_minutes is not None
            and self.sign_out_open_delay_minutes > self.sign_out_grace_minutes
        ):
            raise ValueError(
                "sign_out_open_delay_minutes cannot be greater than sign_out_grace_minutes."
            )
        return self

class Event(EventBase):
    id: int
    school_id: int
    present_until_override_at: Optional[datetime] = None
    late_until_override_at: Optional[datetime] = None
    sign_out_override_until: Optional[datetime] = None
    departments: List[Department] = Field(default_factory=list)
    programs: List[Program] = Field(default_factory=list)
    event_targets: List[EventTarget] = Field(default_factory=list)
    event_type: Optional[EventTypeSummary] = None
    
    # Computed fields for IDs
    @computed_field
    def department_ids(self) -> List[int]:
        return [dept.id for dept in self.departments]
    
    @computed_field
    def program_ids(self) -> List[int]:
        return [program.id for program in self.programs]
    
    model_config = ConfigDict(from_attributes=True)

class EventWithRelations(Event):
    departments: List[Department] = Field(default_factory=list)
    programs: List[Program] = Field(default_factory=list)
    attendances: List[Attendance] = Field(
        default_factory=list,
        description="Attendance records for this event"
    )
    attendance_summary: dict = Field(
        default_factory=dict,
        description="Counts by attendance status"
    )
    
    model_config = ConfigDict(from_attributes=True)

class EventPaginated(BaseModel):
    total: int
    items: List[Event]
    skip: int
    limit: int

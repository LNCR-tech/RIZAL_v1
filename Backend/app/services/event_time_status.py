from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_EVENT_TIMEZONE = "Asia/Manila"


@dataclass(frozen=True)
class EventTimeStatusResult:
    event_status: str
    current_time: datetime
    start_time: datetime
    end_time: datetime
    late_threshold_time: datetime
    timezone_name: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AttendanceDecisionResult:
    event_status: str
    attendance_allowed: bool
    attendance_status: str | None
    reason_code: str | None
    message: str
    current_time: datetime
    start_time: datetime
    end_time: datetime
    late_threshold_time: datetime
    timezone_name: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_event_timezone(timezone_name: str = DEFAULT_EVENT_TIMEZONE) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unsupported timezone: {timezone_name}") from exc


def normalize_event_datetime(
    value: datetime,
    timezone_name: str = DEFAULT_EVENT_TIMEZONE,
) -> datetime:
    zone = get_event_timezone(timezone_name)
    if value.tzinfo is None:
        return value.replace(tzinfo=zone)
    return value.astimezone(zone)


def normalize_late_threshold_minutes(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        threshold = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, threshold)


def get_event_status(
    *,
    start_time: datetime,
    end_time: datetime,
    late_threshold_minutes: Any = 0,
    current_time: datetime | None = None,
    timezone_name: str = DEFAULT_EVENT_TIMEZONE,
) -> EventTimeStatusResult:
    zone = get_event_timezone(timezone_name)
    localized_start = normalize_event_datetime(start_time, timezone_name)
    localized_end = normalize_event_datetime(end_time, timezone_name)
    if localized_end <= localized_start:
        raise ValueError("end_time must be after start_time")

    if current_time is None:
        localized_now = datetime.now(zone)
    else:
        localized_now = normalize_event_datetime(current_time, timezone_name)

    late_threshold_time = localized_start + timedelta(
        minutes=normalize_late_threshold_minutes(late_threshold_minutes)
    )

    if localized_now < localized_start:
        event_status = "upcoming"
    elif localized_now >= localized_end:
        event_status = "closed"
    elif localized_now <= late_threshold_time:
        event_status = "open"
    else:
        event_status = "late"

    return EventTimeStatusResult(
        event_status=event_status,
        current_time=localized_now,
        start_time=localized_start,
        end_time=localized_end,
        late_threshold_time=late_threshold_time,
        timezone_name=timezone_name,
    )


def get_attendance_decision(
    *,
    start_time: datetime,
    end_time: datetime,
    late_threshold_minutes: Any = 0,
    current_time: datetime | None = None,
    timezone_name: str = DEFAULT_EVENT_TIMEZONE,
) -> AttendanceDecisionResult:
    event_status = get_event_status(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=late_threshold_minutes,
        current_time=current_time,
        timezone_name=timezone_name,
    )

    if event_status.event_status == "upcoming":
        return AttendanceDecisionResult(
            event_status=event_status.event_status,
            attendance_allowed=False,
            attendance_status=None,
            reason_code="event_not_open_yet",
            message="Attendance is not open yet for this event.",
            current_time=event_status.current_time,
            start_time=event_status.start_time,
            end_time=event_status.end_time,
            late_threshold_time=event_status.late_threshold_time,
            timezone_name=event_status.timezone_name,
        )

    if event_status.event_status == "closed":
        return AttendanceDecisionResult(
            event_status=event_status.event_status,
            attendance_allowed=False,
            attendance_status=None,
            reason_code="event_closed",
            message="Attendance is already closed for this event.",
            current_time=event_status.current_time,
            start_time=event_status.start_time,
            end_time=event_status.end_time,
            late_threshold_time=event_status.late_threshold_time,
            timezone_name=event_status.timezone_name,
        )

    attendance_status = "present" if event_status.event_status == "open" else "late"
    message = (
        "Attendance is open. A valid verification will be marked present."
        if attendance_status == "present"
        else "Attendance is still allowed, but it will be marked late."
    )

    return AttendanceDecisionResult(
        event_status=event_status.event_status,
        attendance_allowed=True,
        attendance_status=attendance_status,
        reason_code=None,
        message=message,
        current_time=event_status.current_time,
        start_time=event_status.start_time,
        end_time=event_status.end_time,
        late_threshold_time=event_status.late_threshold_time,
        timezone_name=event_status.timezone_name,
    )

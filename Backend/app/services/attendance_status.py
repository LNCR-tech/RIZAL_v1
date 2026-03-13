from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from app.services.event_time_status import (
    DEFAULT_EVENT_TIMEZONE,
    get_event_timezone,
    normalize_event_datetime,
    normalize_late_threshold_minutes,
)


ALL_ATTENDANCE_STATUS_VALUES: tuple[str, ...] = ("present", "late", "absent", "excused")
ATTENDED_STATUS_VALUES: tuple[str, ...] = ("present", "late")


def normalize_attendance_status(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        value = value.value
    return str(value).strip().lower()


def is_attended_status(value: Any) -> bool:
    return normalize_attendance_status(value) in ATTENDED_STATUS_VALUES


def empty_attendance_status_counts() -> dict[str, int]:
    return {status: 0 for status in ALL_ATTENDANCE_STATUS_VALUES}


def normalize_attendance_datetime(
    value: datetime,
    timezone_name: str = DEFAULT_EVENT_TIMEZONE,
) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(get_event_timezone(timezone_name))


def late_cutoff_datetime(
    event_start: datetime,
    late_threshold_minutes: Any,
    timezone_name: str = DEFAULT_EVENT_TIMEZONE,
) -> datetime:
    localized_start = normalize_event_datetime(event_start, timezone_name)
    return localized_start + timedelta(minutes=normalize_late_threshold_minutes(late_threshold_minutes))


def is_late_arrival(
    *,
    event_start: datetime,
    time_in: datetime,
    late_threshold_minutes: Any,
    timezone_name: str = DEFAULT_EVENT_TIMEZONE,
) -> bool:
    localized_time_in = normalize_attendance_datetime(time_in, timezone_name)
    return localized_time_in > late_cutoff_datetime(
        event_start,
        late_threshold_minutes,
        timezone_name=timezone_name,
    )


def resolve_time_in_status(
    *,
    event_start: datetime,
    time_in: datetime,
    late_threshold_minutes: Any,
    timezone_name: str = DEFAULT_EVENT_TIMEZONE,
) -> str:
    if is_late_arrival(
        event_start=event_start,
        time_in=time_in,
        late_threshold_minutes=late_threshold_minutes,
        timezone_name=timezone_name,
    ):
        return "late"
    return "present"


def attendance_window_overlaps_event(
    *,
    event_start: datetime,
    event_end: datetime,
    time_in: datetime | None,
    time_out: datetime | None,
    timezone_name: str = DEFAULT_EVENT_TIMEZONE,
) -> bool:
    if time_in is None or time_out is None:
        return False
    localized_start = normalize_event_datetime(event_start, timezone_name)
    localized_end = normalize_event_datetime(event_end, timezone_name)
    localized_time_in = normalize_attendance_datetime(time_in, timezone_name)
    localized_time_out = normalize_attendance_datetime(time_out, timezone_name)
    if localized_time_out <= localized_time_in:
        return False
    overlap_start = max(localized_time_in, localized_start)
    overlap_end = min(localized_time_out, localized_end)
    return overlap_end > overlap_start


def finalize_completed_attendance_status(
    *,
    event_start: datetime,
    event_end: datetime,
    time_in: datetime,
    time_out: datetime,
    late_threshold_minutes: Any,
    timezone_name: str = DEFAULT_EVENT_TIMEZONE,
) -> tuple[str, str | None]:
    if not attendance_window_overlaps_event(
        event_start=event_start,
        event_end=event_end,
        time_in=time_in,
        time_out=time_out,
        timezone_name=timezone_name,
    ):
        return (
            "absent",
            "Sign-in and sign-out were recorded, but the attendance window did not align with the event schedule.",
        )

    final_status = resolve_time_in_status(
        event_start=event_start,
        time_in=time_in,
        late_threshold_minutes=late_threshold_minutes,
        timezone_name=timezone_name,
    )
    return final_status, None

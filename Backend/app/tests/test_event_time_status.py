from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.services.event_time_status import (
    get_attendance_decision,
    get_event_status,
)


def test_get_event_status_transitions_across_time_windows() -> None:
    manila = ZoneInfo("Asia/Manila")
    start_time = datetime(2026, 3, 11, 9, 0, 0)
    end_time = datetime(2026, 3, 11, 11, 0, 0)

    upcoming = get_event_status(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        current_time=datetime(2026, 3, 11, 8, 59, 0, tzinfo=manila),
    )
    open_status = get_event_status(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        current_time=datetime(2026, 3, 11, 9, 10, 0, tzinfo=manila),
    )
    late_status = get_event_status(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        current_time=datetime(2026, 3, 11, 9, 10, 1, tzinfo=manila),
    )
    closed = get_event_status(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        current_time=datetime(2026, 3, 11, 11, 0, 0, tzinfo=manila),
    )

    assert upcoming.event_status == "upcoming"
    assert open_status.event_status == "open"
    assert late_status.event_status == "late"
    assert closed.event_status == "closed"


def test_get_event_status_supports_naive_event_datetimes_and_returns_manila_zone() -> None:
    result = get_event_status(
        start_time=datetime(2026, 3, 11, 9, 0, 0),
        end_time=datetime(2026, 3, 11, 11, 0, 0),
        late_threshold_minutes=15,
        current_time=datetime(2026, 3, 11, 9, 5, 0),
    )

    assert result.event_status == "open"
    assert result.timezone_name == "Asia/Manila"
    assert str(result.current_time.tzinfo) == "Asia/Manila"


def test_get_attendance_decision_maps_event_status_to_attendance_result() -> None:
    manila = ZoneInfo("Asia/Manila")
    start_time = datetime(2026, 3, 11, 9, 0, 0)
    end_time = datetime(2026, 3, 11, 11, 0, 0)

    upcoming = get_attendance_decision(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        current_time=datetime(2026, 3, 11, 8, 0, 0, tzinfo=manila),
    )
    open_decision = get_attendance_decision(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        current_time=datetime(2026, 3, 11, 9, 1, 0, tzinfo=manila),
    )
    late_decision = get_attendance_decision(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        current_time=datetime(2026, 3, 11, 9, 20, 0, tzinfo=manila),
    )
    closed = get_attendance_decision(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        current_time=datetime(2026, 3, 11, 11, 30, 0, tzinfo=manila),
    )

    assert upcoming.attendance_allowed is False
    assert upcoming.reason_code == "event_not_open_yet"
    assert open_decision.attendance_allowed is True
    assert open_decision.attendance_status == "present"
    assert late_decision.attendance_allowed is True
    assert late_decision.attendance_status == "late"
    assert closed.attendance_allowed is False
    assert closed.reason_code == "event_closed"


def test_get_event_status_rejects_invalid_schedule() -> None:
    with pytest.raises(ValueError, match="end_time must be after start_time"):
        get_event_status(
            start_time=datetime(2026, 3, 11, 11, 0, 0),
            end_time=datetime(2026, 3, 11, 11, 0, 0),
            late_threshold_minutes=10,
        )

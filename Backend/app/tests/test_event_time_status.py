"""Use: Tests computed event time status rules.
Where to use: Use this when running `pytest` to check that this backend behavior still works.
Role: Test layer. It protects the app from regressions.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.services.event_time_status import (
    get_attendance_decision,
    get_effective_sign_out_close_time,
    get_event_status,
    get_sign_out_decision,
)


def test_get_event_status_transitions_across_all_windows() -> None:
    manila = ZoneInfo("Asia/Manila")
    start_time = datetime(2026, 3, 11, 9, 0, 0)
    end_time = datetime(2026, 3, 11, 11, 0, 0)

    before_check_in = get_event_status(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 8, 49, 59, tzinfo=manila),
    )
    early_check_in = get_event_status(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 8, 50, 0, tzinfo=manila),
    )
    late_check_in = get_event_status(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 9, 10, 0, tzinfo=manila),
    )
    absent_check_in = get_event_status(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 9, 10, 1, tzinfo=manila),
    )
    sign_out_open = get_event_status(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 11, 5, 0, tzinfo=manila),
    )
    closed = get_event_status(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 11, 10, 1, tzinfo=manila),
    )

    assert before_check_in.event_status == "before_check_in"
    assert early_check_in.event_status == "early_check_in"
    assert late_check_in.event_status == "late_check_in"
    assert absent_check_in.event_status == "absent_check_in"
    assert sign_out_open.event_status == "sign_out_open"
    assert closed.event_status == "closed"
    assert early_check_in.check_in_opens_at == datetime(
        2026, 3, 11, 8, 50, 0, tzinfo=manila
    )
    assert sign_out_open.effective_sign_out_closes_at == datetime(
        2026, 3, 11, 11, 10, 0, tzinfo=manila
    )


def test_get_event_status_supports_naive_event_datetimes_and_returns_manila_zone() -> None:
    result = get_event_status(
        start_time=datetime(2026, 3, 11, 9, 0, 0),
        end_time=datetime(2026, 3, 11, 11, 0, 0),
        early_check_in_minutes=15,
        late_threshold_minutes=15,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 9, 5, 0),
    )

    assert result.event_status == "late_check_in"
    assert result.timezone_name == "Asia/Manila"
    assert str(result.current_time.tzinfo) == "Asia/Manila"
    assert result.sign_out_opens_at.isoformat() == "2026-03-11T11:00:00+08:00"


def test_get_attendance_decision_maps_check_in_windows_to_statuses() -> None:
    manila = ZoneInfo("Asia/Manila")
    start_time = datetime(2026, 3, 11, 9, 0, 0)
    end_time = datetime(2026, 3, 11, 11, 0, 0)

    before_check_in = get_attendance_decision(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 8, 45, 0, tzinfo=manila),
    )
    early_check_in = get_attendance_decision(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 8, 55, 0, tzinfo=manila),
    )
    late_check_in = get_attendance_decision(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 9, 0, 0, tzinfo=manila),
    )
    absent_check_in = get_attendance_decision(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 9, 20, 0, tzinfo=manila),
    )
    sign_out_open = get_attendance_decision(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 11, 0, 0, tzinfo=manila),
    )
    closed = get_attendance_decision(
        start_time=start_time,
        end_time=end_time,
        early_check_in_minutes=10,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 11, 10, 1, tzinfo=manila),
    )

    assert before_check_in.attendance_allowed is False
    assert before_check_in.reason_code == "event_not_open_yet"

    assert early_check_in.attendance_allowed is True
    assert early_check_in.attendance_status == "present"

    assert late_check_in.attendance_allowed is True
    assert late_check_in.attendance_status == "late"

    assert absent_check_in.attendance_allowed is True
    assert absent_check_in.attendance_status == "absent"

    assert sign_out_open.attendance_allowed is False
    assert sign_out_open.reason_code == "sign_out_window_open"

    assert closed.attendance_allowed is False
    assert closed.reason_code == "event_closed"


def test_get_sign_out_decision_respects_override_and_grace_windows() -> None:
    manila = ZoneInfo("Asia/Manila")
    start_time = datetime(2026, 3, 11, 9, 0, 0)
    end_time = datetime(2026, 3, 11, 11, 0, 0)

    before_sign_out = get_sign_out_decision(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 10, 59, 59, tzinfo=manila),
    )
    normal_sign_out = get_sign_out_decision(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        current_time=datetime(2026, 3, 11, 11, 5, 0, tzinfo=manila),
    )
    override_sign_out = get_sign_out_decision(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        sign_out_override_until=datetime(2026, 3, 11, 9, 20, 0),
        current_time=datetime(2026, 3, 11, 9, 5, 0, tzinfo=manila),
    )
    override_expired_before_end = get_sign_out_decision(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        sign_out_override_until=datetime(2026, 3, 11, 9, 20, 0),
        current_time=datetime(2026, 3, 11, 9, 25, 0, tzinfo=manila),
    )
    overlapping_override = get_sign_out_decision(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        sign_out_override_until=datetime(2026, 3, 11, 11, 15, 0),
        current_time=datetime(2026, 3, 11, 11, 12, 0, tzinfo=manila),
    )
    closed = get_sign_out_decision(
        start_time=start_time,
        end_time=end_time,
        late_threshold_minutes=10,
        sign_out_grace_minutes=10,
        sign_out_override_until=datetime(2026, 3, 11, 11, 15, 0),
        current_time=datetime(2026, 3, 11, 11, 15, 1, tzinfo=manila),
    )

    assert before_sign_out.attendance_allowed is False
    assert before_sign_out.reason_code == "sign_out_not_open_yet"

    assert normal_sign_out.attendance_allowed is True
    assert normal_sign_out.attendance_status == "present"

    assert override_sign_out.attendance_allowed is True
    assert override_sign_out.event_status == "sign_out_open"
    assert override_sign_out.sign_out_override_active is True

    assert override_expired_before_end.attendance_allowed is False
    assert override_expired_before_end.reason_code == "sign_out_not_open_yet"
    assert override_expired_before_end.event_status == "absent_check_in"

    assert overlapping_override.attendance_allowed is True
    assert overlapping_override.sign_out_override_active is True
    assert get_effective_sign_out_close_time(
        end_time,
        sign_out_grace_minutes=10,
        sign_out_override_until=datetime(2026, 3, 11, 11, 15, 0),
    ) == datetime(2026, 3, 11, 11, 15, 0, tzinfo=manila)

    assert closed.attendance_allowed is False
    assert closed.reason_code == "sign_out_closed"


def test_get_event_status_rejects_invalid_schedule() -> None:
    with pytest.raises(ValueError, match="end_time must be after start_time"):
        get_event_status(
            start_time=datetime(2026, 3, 11, 11, 0, 0),
            end_time=datetime(2026, 3, 11, 11, 0, 0),
            late_threshold_minutes=10,
        )

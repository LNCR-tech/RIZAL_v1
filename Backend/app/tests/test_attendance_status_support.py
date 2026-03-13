from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.models.attendance import AttendanceStatus as ModelAttendanceStatus
from app.schemas.attendance import (
    AttendanceStatus as SchemaAttendanceStatus,
    ProgramBreakdownItem,
    StudentAttendanceSummary,
)
from app.services.attendance_status import (
    ATTENDED_STATUS_VALUES,
    finalize_completed_attendance_status,
    empty_attendance_status_counts,
    is_late_arrival,
    is_attended_status,
    normalize_attendance_status,
    resolve_time_in_status,
)


def test_model_and_schema_include_late_status() -> None:
    assert ModelAttendanceStatus.LATE.value == "late"
    assert SchemaAttendanceStatus.LATE.value == "late"


def test_late_counts_as_attended() -> None:
    assert ATTENDED_STATUS_VALUES == ("present", "late")
    assert is_attended_status("present") is True
    assert is_attended_status("late") is True
    assert is_attended_status("absent") is False
    assert is_attended_status("excused") is False


def test_empty_status_counts_include_late() -> None:
    assert empty_attendance_status_counts() == {
        "present": 0,
        "late": 0,
        "absent": 0,
        "excused": 0,
    }


def test_normalize_attendance_status_handles_enum_values() -> None:
    assert normalize_attendance_status(SchemaAttendanceStatus.LATE) == "late"
    assert normalize_attendance_status(ModelAttendanceStatus.PRESENT) == "present"


def test_report_models_accept_late_fields() -> None:
    summary = StudentAttendanceSummary(
        student_id="2024-0001",
        student_name="Test Student",
        total_events=4,
        attended_events=3,
        late_events=1,
        absent_events=1,
        excused_events=0,
        attendance_rate=75.0,
    )
    breakdown = ProgramBreakdownItem(
        program="BSIT",
        total=10,
        present=5,
        late=1,
        absent=4,
    )

    assert summary.late_events == 1
    assert breakdown.late == 1


def test_late_threshold_helpers() -> None:
    event_start = datetime(2026, 3, 11, 9, 0, 0)
    on_time_scan = datetime(2026, 3, 11, 1, 5, 0)
    late_scan = datetime(2026, 3, 11, 1, 11, 0)

    assert is_late_arrival(
        event_start=event_start,
        time_in=on_time_scan,
        late_threshold_minutes=10,
    ) is False
    assert is_late_arrival(
        event_start=event_start,
        time_in=late_scan,
        late_threshold_minutes=10,
    ) is True
    assert (
        resolve_time_in_status(
            event_start=event_start,
            time_in=late_scan,
            late_threshold_minutes=10,
        )
        == "late"
    )


def test_finalize_completed_attendance_status_respects_late_threshold() -> None:
    status_value, note = finalize_completed_attendance_status(
        event_start=datetime(2026, 3, 11, 9, 0, 0),
        event_end=datetime(2026, 3, 11, 11, 0, 0),
        time_in=datetime(2026, 3, 11, 1, 15, 0),
        time_out=datetime(2026, 3, 11, 2, 0, 0),
        late_threshold_minutes=10,
    )

    assert status_value == "late"
    assert note is None


def test_finalize_completed_attendance_status_marks_absent_without_overlap() -> None:
    status_value, note = finalize_completed_attendance_status(
        event_start=datetime(2026, 3, 11, 9, 0, 0),
        event_end=datetime(2026, 3, 11, 11, 0, 0),
        time_in=datetime(2026, 3, 11, 3, 30, 0),
        time_out=datetime(2026, 3, 11, 3, 45, 0),
        late_threshold_minutes=10,
    )

    assert status_value == "absent"
    assert note is not None


def test_late_threshold_helpers_support_aware_utc_timestamps() -> None:
    manila = ZoneInfo("Asia/Manila")
    event_start = datetime(2026, 3, 11, 9, 0, 0, tzinfo=manila)
    late_scan = datetime(2026, 3, 11, 1, 20, 0, tzinfo=timezone.utc)

    assert (
        resolve_time_in_status(
            event_start=event_start,
            time_in=late_scan,
            late_threshold_minutes=10,
        )
        == "late"
    )

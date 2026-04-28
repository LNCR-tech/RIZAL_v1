from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.attendance_status import resolve_attendance_display_status


def test_signed_in_without_sign_out_displays_absent_even_when_stored_present():
    time_in = datetime(2026, 4, 29, 8, 0, tzinfo=timezone.utc)

    assert (
        resolve_attendance_display_status(
            stored_status="present",
            time_in=time_in,
            time_out=None,
        )
        == "absent"
    )


def test_completed_attendance_preserves_present_or_late_status():
    time_in = datetime(2026, 4, 29, 8, 0, tzinfo=timezone.utc)
    time_out = datetime(2026, 4, 29, 10, 0, tzinfo=timezone.utc)

    assert (
        resolve_attendance_display_status(
            stored_status="late",
            time_in=time_in,
            time_out=time_out,
        )
        == "late"
    )


def test_never_signed_in_uses_terminal_absent_or_excused_status():
    assert (
        resolve_attendance_display_status(
            stored_status="excused",
            time_in=None,
            time_out=None,
        )
        == "excused"
    )

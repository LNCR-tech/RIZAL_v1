"""Use: Tests event geolocation service behavior.
Where to use: Use this when running `pytest` to check that this backend behavior still works.
Role: Test layer. It protects the app from regressions.
"""

from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.event_geolocation import (
    validate_event_geolocation_fields,
    verify_event_geolocation,
    verify_event_geolocation_for_attendance,
)


def _build_event(**overrides):
    payload = {
        "geo_latitude": 8.1575,
        "geo_longitude": 123.8431,
        "geo_radius_m": 30.0,
        "geo_required": True,
        "geo_max_accuracy_m": 20.0,
        "start_datetime": datetime(2026, 3, 11, 9, 0, 0),
        "end_datetime": datetime(2026, 3, 11, 11, 0, 0),
        "late_threshold_minutes": 10,
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


def test_validate_event_geolocation_fields_requires_complete_triplet() -> None:
    with pytest.raises(HTTPException, match="latitude, longitude, and radius together"):
        validate_event_geolocation_fields(
            latitude=8.1575,
            longitude=None,
            radius_m=30.0,
            required=False,
        )


def test_validate_event_geolocation_fields_requires_values_when_enabled() -> None:
    with pytest.raises(HTTPException, match="required when geolocation is enabled"):
        validate_event_geolocation_fields(
            latitude=None,
            longitude=None,
            radius_m=None,
            required=True,
        )


def test_verify_event_geolocation_includes_time_context() -> None:
    response = verify_event_geolocation(
        _build_event(),
        latitude=8.1575,
        longitude=123.8431,
        accuracy_m=5.0,
    )

    assert response.ok is True
    assert response.reason is None
    assert response.time_status is not None
    assert response.time_status.timezone_name == "Asia/Manila"
    assert response.attendance_decision is not None
    assert (
        response.attendance_decision.event_status
        == response.time_status.event_status
    )


def test_verify_event_geolocation_for_attendance_returns_none_when_optional() -> None:
    response = verify_event_geolocation_for_attendance(
        _build_event(
            geo_latitude=None,
            geo_longitude=None,
            geo_radius_m=None,
            geo_required=False,
        ),
        latitude=None,
        longitude=None,
        accuracy_m=None,
    )

    assert response is None


def test_verify_event_geolocation_for_attendance_raises_for_outside_scan() -> None:
    with pytest.raises(HTTPException) as exc_info:
        verify_event_geolocation_for_attendance(
            _build_event(),
            latitude=0.0,
            longitude=0.0,
            accuracy_m=5.0,
        )

    assert exc_info.value.status_code == 403
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["code"] == "event_geolocation_verification_failed"
    assert exc_info.value.detail["message"] == (
        "The current location is not valid for this event attendance scan."
    )
    assert exc_info.value.detail["ok"] is False
    assert exc_info.value.detail["reason"] in {
        "outside_geofence",
        "outside_geofence_buffered",
    }
    assert exc_info.value.detail["time_status"] is not None
    assert exc_info.value.detail["attendance_decision"] is not None


def test_verify_event_geolocation_for_attendance_includes_time_context_when_inside() -> None:
    response = verify_event_geolocation_for_attendance(
        _build_event(),
        latitude=8.1575,
        longitude=123.8431,
        accuracy_m=5.0,
    )

    assert response is not None
    assert response.ok is True
    assert response.time_status is not None
    assert response.attendance_decision is not None


def test_verify_event_geolocation_reports_attendance_override_cutoffs_when_active() -> None:
    response = verify_event_geolocation(
        _build_event(
            early_check_in_minutes=30,
            present_until_override_at=datetime(2026, 3, 11, 9, 29, 0),
            late_until_override_at=datetime(2026, 3, 11, 9, 39, 0),
        ),
        latitude=8.1575,
        longitude=123.8431,
        accuracy_m=5.0,
    )

    assert response.time_status is not None
    assert response.time_status.attendance_override_active is True
    assert response.time_status.effective_present_until_at.isoformat() == (
        "2026-03-11T09:29:00+08:00"
    )
    assert response.time_status.effective_late_until_at.isoformat() == (
        "2026-03-11T09:39:00+08:00"
    )
    assert response.attendance_decision is not None
    assert response.attendance_decision.attendance_override_active is True
    assert response.attendance_decision.effective_present_until_at.isoformat() == (
        "2026-03-11T09:29:00+08:00"
    )
    assert response.attendance_decision.effective_late_until_at.isoformat() == (
        "2026-03-11T09:39:00+08:00"
    )


def test_verify_event_geolocation_for_attendance_requires_coordinates_when_enabled() -> None:
    with pytest.raises(HTTPException) as exc_info:
        verify_event_geolocation_for_attendance(
            _build_event(),
            latitude=None,
            longitude=None,
            accuracy_m=None,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == {
        "code": "event_geolocation_coordinates_required",
        "message": "Latitude and longitude are required for this event.",
    }

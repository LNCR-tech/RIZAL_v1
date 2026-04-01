"""Use: Tests geolocation helpers and edge cases.
Where to use: Use this when running `pytest` to check that this backend behavior still works.
Role: Test layer. It protects the app from regressions.
"""

import pytest

from app.services.geolocation import (
    REASON_ACCURACY_EXCEEDS_LIMIT,
    REASON_ACCURACY_MISSING,
    REASON_GEOFENCE_RADIUS_OUT_OF_RANGE,
    REASON_INVALID_ACCURACY,
    REASON_INVALID_EVENT_COORDINATES,
    REASON_INVALID_GEOFENCE_RADIUS,
    REASON_INVALID_USER_COORDINATES,
    REASON_OUTSIDE_GEOFENCE,
    REASON_OUTSIDE_GEOFENCE_BUFFERED,
    geofence_check,
    haversine_m,
)


def test_haversine_returns_zero_for_same_point():
    assert haversine_m(8.0, 123.0, 8.0, 123.0) == pytest.approx(0.0)


def test_geofence_check_accepts_student_inside_radius():
    result = geofence_check(
        user_lat=8.1575,
        user_lng=123.8431,
        event_lat=8.1575,
        event_lng=123.8431,
        radius_m=30.0,
        accuracy_m=5.0,
    )

    assert result.ok is True
    assert result.reason is None
    assert result.distance_m == pytest.approx(0.0)
    assert result.effective_distance_m == pytest.approx(5.0)


def test_geofence_check_rejects_invalid_user_coordinates():
    result = geofence_check(
        user_lat=91.0,
        user_lng=123.8431,
        event_lat=8.1575,
        event_lng=123.8431,
        radius_m=30.0,
    )

    assert result.ok is False
    assert result.reason == REASON_INVALID_USER_COORDINATES


def test_geofence_check_rejects_invalid_event_coordinates():
    result = geofence_check(
        user_lat=8.1575,
        user_lng=123.8431,
        event_lat=8.1575,
        event_lng=181.0,
        radius_m=30.0,
    )

    assert result.ok is False
    assert result.reason == REASON_INVALID_EVENT_COORDINATES


@pytest.mark.parametrize(
    ("radius_m", "expected_reason"),
    [
        (0.0, REASON_INVALID_GEOFENCE_RADIUS),
        (-1.0, REASON_INVALID_GEOFENCE_RADIUS),
        (5001.0, REASON_GEOFENCE_RADIUS_OUT_OF_RANGE),
    ],
)
def test_geofence_check_rejects_invalid_radius(radius_m, expected_reason):
    result = geofence_check(
        user_lat=8.1575,
        user_lng=123.8431,
        event_lat=8.1575,
        event_lng=123.8431,
        radius_m=radius_m,
    )

    assert result.ok is False
    assert result.reason == expected_reason


def test_geofence_check_requires_accuracy_when_enabled():
    result = geofence_check(
        user_lat=8.1575,
        user_lng=123.8431,
        event_lat=8.1575,
        event_lng=123.8431,
        radius_m=30.0,
        require_accuracy=True,
    )

    assert result.ok is False
    assert result.reason == REASON_ACCURACY_MISSING


@pytest.mark.parametrize("accuracy_m", [0, -1, "bad-value", float("inf")])
def test_geofence_check_handles_invalid_accuracy_safely(accuracy_m):
    result = geofence_check(
        user_lat=8.1575,
        user_lng=123.8431,
        event_lat=8.1575,
        event_lng=123.8431,
        radius_m=30.0,
        accuracy_m=accuracy_m,
    )

    assert result.ok is False
    assert result.reason == REASON_INVALID_ACCURACY


def test_geofence_check_rejects_accuracy_over_limit():
    result = geofence_check(
        user_lat=8.1575,
        user_lng=123.8431,
        event_lat=8.1575,
        event_lng=123.8431,
        radius_m=30.0,
        accuracy_m=45.0,
        max_allowed_accuracy_m=20.0,
    )

    assert result.ok is False
    assert result.reason == REASON_ACCURACY_EXCEEDS_LIMIT


def test_geofence_check_uses_accuracy_buffer_by_default():
    result = geofence_check(
        user_lat=0.00004,
        user_lng=0.0,
        event_lat=0.0,
        event_lng=0.0,
        radius_m=10.0,
        accuracy_m=6.0,
    )

    assert result.ok is False
    assert result.reason == REASON_OUTSIDE_GEOFENCE_BUFFERED
    assert result.distance_m < result.radius_m
    assert result.effective_distance_m > result.radius_m


def test_geofence_check_can_skip_accuracy_buffer_when_needed():
    result = geofence_check(
        user_lat=0.00004,
        user_lng=0.0,
        event_lat=0.0,
        event_lng=0.0,
        radius_m=10.0,
        accuracy_m=6.0,
        use_accuracy_buffer=False,
    )

    assert result.ok is True
    assert result.reason is None
    assert result.distance_m < result.radius_m
    assert result.effective_distance_m == pytest.approx(result.distance_m)


def test_geofence_check_reports_plain_outside_reason_without_accuracy():
    result = geofence_check(
        user_lat=0.0002,
        user_lng=0.0,
        event_lat=0.0,
        event_lng=0.0,
        radius_m=10.0,
    )

    assert result.ok is False
    assert result.reason == REASON_OUTSIDE_GEOFENCE


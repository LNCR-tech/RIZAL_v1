from datetime import datetime, timedelta, timezone

import pytest


def _future_event_payload(name="Edge Case Event", **overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "name": name,
        "start_datetime": (now + timedelta(hours=2)).isoformat(),
        "end_datetime": (now + timedelta(hours=4)).isoformat(),
        "location": "Automation Hall",
        "event_targets": [{"scope_type": "ALL"}],
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    ("target", "expected_detail"),
    [
        ({"scope_type": "YEAR_LEVEL"}, "YEAR_LEVEL scope requires year_level"),
        ({"scope_type": "ALL", "year_level": 1}, "ALL scope cannot have year_level"),
        ({"scope_type": "COURSE_YEAR", "year_level": 2}, "COURSE_YEAR scope requires both"),
        (
            {"scope_type": "DEPARTMENT_YEAR", "department_id": 1},
            "DEPARTMENT_YEAR scope requires both",
        ),
    ],
)
def test_create_event_rejects_invalid_target_field_combinations(
    client,
    campus_admin_headers,
    target,
    expected_detail,
):
    # This protects event creation from accepting audience scopes with missing or contradictory fields.
    response = client.post(
        "/api/events/",
        headers=campus_admin_headers,
        json=_future_event_payload("Invalid Target Combination", event_targets=[target]),
    )

    assert response.status_code == 422
    assert expected_detail in response.text


def test_create_event_rejects_unknown_program_target(client, campus_admin_headers):
    # This protects course-targeted events from referencing programs outside the school dataset.
    response = client.post(
        "/api/events/",
        headers=campus_admin_headers,
        json=_future_event_payload(
            "Unknown Program Target",
            event_targets=[{"scope_type": "COURSE", "course_id": 999999}],
        ),
    )

    assert response.status_code == 400
    assert "Program ID 999999 not found" in response.text


def test_create_event_rejects_incomplete_geofence_fields(client, campus_admin_headers):
    # This protects geolocation-required events from saving only part of the location fence.
    response = client.post(
        "/api/events/",
        headers=campus_admin_headers,
        json=_future_event_payload(
            "Incomplete Geofence Event",
            geo_required=True,
            geo_latitude=8.1552,
            geo_longitude=123.8421,
        ),
    )

    assert response.status_code == 400
    assert "Geofence coordinates and radius are required" in response.text


def test_create_event_rejects_overlong_idempotency_key(client, campus_admin_headers):
    # This protects the idempotent event-create contract from unbounded header values.
    response = client.post(
        "/api/events/",
        headers={
            **campus_admin_headers,
            "X-Idempotency-Key": "x" * 129,
        },
        json=_future_event_payload("Overlong Idempotency Key"),
    )

    assert response.status_code == 400
    assert "must not exceed 128 characters" in response.text


def test_update_event_rejects_empty_replacement_targets(client, campus_admin_headers):
    # This protects event edits from accidentally clearing every target audience.
    create_response = client.post(
        "/api/events/",
        headers=campus_admin_headers,
        json=_future_event_payload("Empty Target Update Seed"),
    )
    assert create_response.status_code in (200, 201), create_response.text

    update_response = client.patch(
        f"/api/events/{create_response.json()['id']}",
        headers=campus_admin_headers,
        json={"event_targets": []},
    )

    assert update_response.status_code == 400
    assert "at least one target audience" in update_response.text


def test_student_report_rejects_invalid_date_filter(client, campus_admin_headers, db_session):
    # This protects report endpoints from accepting malformed date filters.
    from app.models.user import StudentProfile

    profile = db_session.query(StudentProfile).filter_by(student_number="STU-001").first()
    assert profile is not None

    response = client.get(
        f"/api/attendance/students/{profile.id}/report?start_date=not-a-date",
        headers=campus_admin_headers,
    )

    assert response.status_code == 422

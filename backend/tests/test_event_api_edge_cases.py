from datetime import datetime, timedelta, timezone

import pytest


def _future_event_payload(name="Edge Case Event", **overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "name": name,
        "start_datetime": (now + timedelta(hours=2)).isoformat(),
        "end_datetime": (now + timedelta(hours=4)).isoformat(),
        "location": "Automation Hall",
        # Post c2fc7ba the API takes `year_levels: List[int]` (1-5, or empty
        # meaning "everyone"). The old per-target `event_targets: [{...}]`
        # field is gone — department/course scope is now derived from the
        # creator's governance position, never from the request body.
        "year_levels": [],
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    "bad_year_levels",
    [[0], [6], [-1], [3, 99], [10]],
)
def test_create_event_rejects_invalid_year_levels(
    client,
    campus_admin_headers,
    bad_year_levels,
):
    # year_levels is validated by EventCreate.validate_year_levels — each entry
    # must be between 1 and 5 inclusive.
    response = client.post(
        "/api/events/",
        headers=campus_admin_headers,
        json=_future_event_payload(
            "Invalid year_levels",
            year_levels=bad_year_levels,
        ),
    )

    assert response.status_code == 422, response.text
    assert "year_levels" in response.text


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
    assert "latitude, longitude, and radius" in response.text


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


def test_update_event_rejects_invalid_year_levels(client, campus_admin_headers):
    # PATCH path also uses the year_levels validator — same 1–5 bounds.
    create_response = client.post(
        "/api/events/",
        headers=campus_admin_headers,
        json=_future_event_payload("Year-level Update Seed"),
    )
    assert create_response.status_code in (200, 201), create_response.text

    update_response = client.patch(
        f"/api/events/{create_response.json()['id']}",
        headers=campus_admin_headers,
        json={"year_levels": [99]},
    )

    assert update_response.status_code == 422, update_response.text
    assert "year_levels" in update_response.text


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

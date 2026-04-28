"""Tests for untested attendance override endpoints."""
import pytest
from datetime import datetime, timedelta, timezone


@pytest.fixture(scope="module")
def completed_event_id(client, campus_admin_headers, db_session):
    """Create a completed event directly in the DB to bypass past-start API validation."""
    from app.models.event import Event as EventModel, EventStatus as ModelEventStatus
    from app.models.school import School
    from app.models.user import User
    school = db_session.query(School).filter_by(school_code="TEST-001").first()
    actor = db_session.query(User).filter_by(email="campus_admin@test.com").first()
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    event = EventModel(
        school_id=school.id,
        created_by_user_id=actor.id,
        name="Override Test Event",
        location="Test Hall",
        start_datetime=now - timedelta(hours=3),
        end_datetime=now - timedelta(hours=1),
        early_check_in_minutes=30,
        late_threshold_minutes=10,
        sign_out_grace_minutes=20,
        status=ModelEventStatus.COMPLETED,
    )
    db_session.add(event)
    db_session.flush()
    return event.id


def test_mark_excused(client, campus_admin_headers, completed_event_id):
    r = client.post(
        f"/api/attendance/events/{completed_event_id}/mark-excused",
        headers=campus_admin_headers,
        json={"student_ids": ["STU-001"], "reason": "Medical"},
    )
    assert r.status_code == 200
    assert "message" in r.json()


def test_mark_excused_requires_auth(client, completed_event_id):
    r = client.post(
        f"/api/attendance/events/{completed_event_id}/mark-excused",
        json={"student_ids": ["STU-001"], "reason": "Medical"},
    )
    assert r.status_code == 401


def test_mark_excused_not_found(client, campus_admin_headers):
    r = client.post(
        "/api/attendance/events/999999/mark-excused",
        headers=campus_admin_headers,
        json={"student_ids": ["STU-001"], "reason": "Medical"},
    )
    assert r.status_code == 404


def test_mark_absent_no_timeout(client, campus_admin_headers, completed_event_id):
    r = client.post(
        "/api/attendance/mark-absent-no-timeout",
        headers=campus_admin_headers,
        json={"event_id": completed_event_id},
    )
    assert r.status_code == 200
    data = r.json()
    assert "updated_count" in data
    assert data["event_id"] == completed_event_id


def test_mark_absent_no_timeout_requires_auth(client, completed_event_id):
    r = client.post(
        "/api/attendance/mark-absent-no-timeout",
        json={"event_id": completed_event_id},
    )
    assert r.status_code == 401


def test_mark_absent_no_timeout_non_completed_event(client, campus_admin_headers):
    now = datetime.now(timezone.utc)
    r = client.post("/api/events/", headers=campus_admin_headers, json={
        "name": "Upcoming Override Event",
        "start_datetime": (now + timedelta(hours=1)).isoformat(),
        "end_datetime": (now + timedelta(hours=3)).isoformat(),
        "location": "Test Hall",
    })
    assert r.status_code in (200, 201)
    eid = r.json()["id"]
    r2 = client.post(
        "/api/attendance/mark-absent-no-timeout",
        headers=campus_admin_headers,
        json={"event_id": eid},
    )
    assert r2.status_code == 400


def test_mark_absent_no_timeout_missing_event_id(client, campus_admin_headers):
    r = client.post(
        "/api/attendance/mark-absent-no-timeout",
        headers=campus_admin_headers,
        json={},
    )
    assert r.status_code == 422

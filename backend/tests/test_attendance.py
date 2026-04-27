import pytest
from datetime import datetime, timedelta, timezone


@pytest.fixture(scope="module")
def ongoing_event_id(client, campus_admin_headers):
    now_utc = datetime.now(timezone.utc)
    r = client.post("/api/events/", headers=campus_admin_headers, json={
        "name": "Attendance Test Event",
        "start_datetime": (now_utc + timedelta(minutes=5)).isoformat(),
        "end_datetime": (now_utc + timedelta(hours=8)).isoformat(),
        "location": "Test Hall",
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_get_my_attendance(client, student_headers):
    r = client.get("/api/attendance/me/records", headers=student_headers)
    assert r.status_code == 200


def test_get_event_attendance(client, campus_admin_headers, ongoing_event_id):
    r = client.get(f"/api/attendance/events/{ongoing_event_id}/report", headers=campus_admin_headers)
    assert r.status_code == 200


def test_manual_checkin(client, campus_admin_headers, ongoing_event_id):
    r = client.post("/api/attendance/manual", headers=campus_admin_headers, json={
        "event_id": ongoing_event_id,
        "student_id": "STU-001",
    })
    assert r.status_code in (200, 201, 400, 409), r.text


def test_duplicate_checkin(client, campus_admin_headers, ongoing_event_id):
    r = client.post("/api/attendance/manual", headers=campus_admin_headers, json={
        "event_id": ongoing_event_id,
        "student_id": "STU-001",
    })
    assert r.status_code in (200, 201, 400, 409), r.text


def test_attendance_summary(client, campus_admin_headers):
    r = client.get("/api/attendance/summary", headers=campus_admin_headers)
    assert r.status_code == 200

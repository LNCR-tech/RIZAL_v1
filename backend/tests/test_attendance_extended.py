import pytest


@pytest.fixture(scope="module")
def event_id(client, campus_admin_headers, db_session):
    from app.models.event import Event
    event = db_session.query(Event).first()
    if event is None:
        pytest.skip("No events in test DB")
    return event.id


@pytest.fixture(scope="module")
def student_number(db_session):
    from app.models.user import StudentProfile
    profile = db_session.query(StudentProfile).first()
    if profile is None:
        pytest.skip("No student profiles in test DB")
    return profile.student_number


def test_bulk_attendance_requires_auth(client):
    r = client.post("/api/attendance/bulk", json={"records": []})
    assert r.status_code == 401


def test_bulk_attendance(client, campus_admin_headers, event_id, student_number):
    r = client.post("/api/attendance/bulk", headers=campus_admin_headers, json={
        "records": [{"event_id": event_id, "student_id": student_number}]
    })
    assert r.status_code in (200, 409)


def test_mark_excused_requires_auth(client, event_id):
    r = client.post(f"/api/attendance/events/{event_id}/mark-excused",
                    json={"student_ids": [], "reason": "test"})
    assert r.status_code == 401


def test_mark_excused(client, campus_admin_headers, event_id, student_number):
    r = client.post(f"/api/attendance/events/{event_id}/mark-excused",
                    headers=campus_admin_headers,
                    json={"student_ids": [student_number], "reason": "Medical"})
    assert r.status_code in (200, 403, 404)


def test_mark_absent_no_timeout_requires_auth(client):
    r = client.post("/api/attendance/mark-absent-no-timeout", json={"event_id": 1})
    assert r.status_code == 401


def test_face_scan_timeout_requires_auth(client):
    r = client.post("/api/attendance/face-scan-timeout",
                    params={"event_id": 1, "student_id": "STU-001"})
    assert r.status_code == 401


def test_attendance_records_requires_auth(client):
    r = client.get("/api/attendance/students/records")
    assert r.status_code == 401


def test_attendance_overview_requires_auth(client):
    r = client.get("/api/attendance/students/overview")
    assert r.status_code == 401


def test_event_attendance_report(client, campus_admin_headers, event_id):
    r = client.get(f"/api/attendance/events/{event_id}/report", headers=campus_admin_headers)
    assert r.status_code == 200


def test_student_attendance_report(client, campus_admin_headers, db_session):
    from app.models.user import StudentProfile
    profile = db_session.query(StudentProfile).first()
    if profile is None:
        pytest.skip("No student profiles in test DB")
    r = client.get(f"/api/attendance/students/{profile.id}/report", headers=campus_admin_headers)
    assert r.status_code == 200


def test_student_attendance_stats(client, campus_admin_headers, db_session):
    from app.models.user import StudentProfile
    profile = db_session.query(StudentProfile).first()
    if profile is None:
        pytest.skip("No student profiles in test DB")
    r = client.get(f"/api/attendance/students/{profile.id}/stats", headers=campus_admin_headers)
    assert r.status_code in (200, 404)

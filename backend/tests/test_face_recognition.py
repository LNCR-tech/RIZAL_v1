import pytest


def test_face_register_requires_auth(client):
    r = client.post("/api/face/register", json={"image_base64": "data:image/jpeg;base64,/9j/fake"})
    assert r.status_code == 401


def test_face_register_student_only(client, campus_admin_headers):
    # Non-student should get 403
    r = client.post("/api/face/register", headers=campus_admin_headers, json={"image_base64": "fake"})
    assert r.status_code == 403


def test_face_scan_with_recognition_requires_student(client, campus_admin_headers, db_session):
    from app.models.event import Event
    event = db_session.query(Event).first()
    if event is None:
        pytest.skip("No events in test DB")

    r = client.post("/api/face/face-scan-with-recognition", headers=campus_admin_headers, json={
        "event_id": event.id, "image_base64": None,
    })
    assert r.status_code == 403


def test_face_scan_with_recognition_requires_auth(client):
    r = client.post("/api/face/face-scan-with-recognition", json={"event_id": 1, "image_base64": None})
    assert r.status_code == 401

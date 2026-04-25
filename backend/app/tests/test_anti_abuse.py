from __future__ import annotations

from types import SimpleNamespace

from app.core.rate_limit import reset_rate_limit_state
from app.core.security import get_current_student_user
from app.main import app


def test_login_rate_limit_returns_429(client, monkeypatch):
    reset_rate_limit_state()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_COUNT", "1")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_WINDOW_SECONDS", "60")

    payload = {"email": "missing@example.edu", "password": "wrong-password"}
    first = client.post("/login", json=payload)
    second = client.post("/login", json=payload)

    assert first.status_code == 401
    assert second.status_code == 429
    assert second.json()["detail"]["code"] == "rate_limit_exceeded"
    assert int(second.headers["Retry-After"]) > 0


def test_public_attendance_nearby_rejects_invalid_payload(client):
    response = client.post(
        "/public-attendance/events/nearby",
        json={"latitude": 120, "longitude": 121.0},
    )

    assert response.status_code == 422


def test_face_upload_rejects_non_image_content_type(client):
    app.dependency_overrides[get_current_student_user] = lambda: SimpleNamespace(
        id=1,
        email="student.upload@example.edu",
        student_profile=SimpleNamespace(student_id="STU-UPLOAD"),
    )
    try:
        response = client.post(
            "/api/face/register-upload",
            files={"file": ("face.txt", b"not-an-image", "text/plain")},
        )
    finally:
        app.dependency_overrides.pop(get_current_student_user, None)

    assert response.status_code == 415
    assert response.json()["detail"] == "Face uploads must use an image content type."

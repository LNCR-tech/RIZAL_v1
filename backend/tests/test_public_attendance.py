"""Tests for public attendance kiosk endpoints."""


def test_nearby_events_no_matches(client):
    """Valid request with coordinates that won't match any geo-fenced event."""
    r = client.post("/public-attendance/events/nearby", json={
        "latitude": 0.0,
        "longitude": 0.0,
        "accuracy_m": 10.0,
    })
    # Either 200 with empty list (feature enabled) or 404 (feature disabled)
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.json()
        assert "events" in data
        assert isinstance(data["events"], list)


def test_nearby_events_missing_coords(client):
    r = client.post("/public-attendance/events/nearby", json={})
    assert r.status_code == 422


def test_multi_face_scan_disabled_or_not_found(client):
    """Non-existent event should return 404 (or 404 if feature disabled)."""
    r = client.post("/public-attendance/events/999999/multi-face-scan", json={
        "image_base64": "ZmFrZQ==",
        "latitude": 0.0,
        "longitude": 0.0,
        "accuracy_m": 10.0,
        "threshold": 0.5,
        "cooldown_student_ids": [],
    })
    assert r.status_code in (404, 409, 422)


def test_multi_face_scan_missing_body(client):
    r = client.post("/public-attendance/events/1/multi-face-scan", json={})
    assert r.status_code == 422

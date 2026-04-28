def test_get_notification_preferences(client, student_headers):
    r = client.get("/api/notifications/preferences/me", headers=student_headers)
    assert r.status_code == 200


def test_update_notification_preferences(client, student_headers):
    r = client.put("/api/notifications/preferences/me", headers=student_headers, json={
        "email_enabled": True,
        "notify_missed_events": True,
    })
    assert r.status_code == 200


def test_notification_test(client, campus_admin_headers):
    r = client.post("/api/notifications/test", headers=campus_admin_headers, json={
        "message": "Test notification",
    })
    assert r.status_code == 200


def test_public_attendance_nearby_events(client):
    r = client.post("/public-attendance/events/nearby", json={
        "latitude": 14.5995,
        "longitude": 120.9842,
        "accuracy_m": 10.0,
    })
    # Either returns events or 404 if public attendance is disabled
    assert r.status_code in (200, 404, 429)


def test_health_readiness(client):
    r = client.get("/health/readiness")
    assert r.status_code in (200, 503)

def test_dispatch_missed_events(client, campus_admin_headers):
    r = client.post("/api/notifications/dispatch/missed-events", headers=campus_admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "processed_users" in data


def test_dispatch_low_attendance(client, campus_admin_headers):
    r = client.post("/api/notifications/dispatch/low-attendance", headers=campus_admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "processed_users" in data


def test_notification_inbox_me(client, student_headers):
    r = client.get("/api/notifications/inbox/me", headers=student_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_dispatch_requires_admin(client, student_headers):
    r = client.post("/api/notifications/dispatch/missed-events", headers=student_headers)
    assert r.status_code == 403


def test_dispatch_requires_auth(client):
    r = client.post("/api/notifications/dispatch/missed-events")
    assert r.status_code == 401

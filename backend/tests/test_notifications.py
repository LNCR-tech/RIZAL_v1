def test_list_notifications(client, student_headers):
    r = client.get("/api/notifications/", headers=student_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_mark_all_read(client, student_headers):
    r = client.post("/api/notifications/mark-all-read", headers=student_headers)
    assert r.status_code in (200, 204)


def test_notifications_require_auth(client):
    r = client.get("/api/notifications/")
    assert r.status_code == 401

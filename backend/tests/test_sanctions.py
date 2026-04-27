def test_list_sanctions(client, campus_admin_headers):
    r = client.get("/api/sanctions/", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_sanctions_require_auth(client):
    r = client.get("/api/sanctions/")
    assert r.status_code == 401


def test_student_can_view_own_sanctions(client, student_headers):
    r = client.get("/api/sanctions/me", headers=student_headers)
    assert r.status_code == 200


def test_student_cannot_manage_sanctions(client, student_headers):
    r = client.post("/api/sanctions/configs/", headers=student_headers, json={
        "event_id": 999,
        "sanctions_enabled": True,
    })
    assert r.status_code == 403

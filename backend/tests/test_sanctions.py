def test_list_sanctions(client, campus_admin_headers):
    r = client.get("/api/sanctions/dashboard", headers=campus_admin_headers)
    assert r.status_code in (200, 403)


def test_sanctions_require_auth(client):
    r = client.get("/api/sanctions/dashboard")
    assert r.status_code == 401


def test_student_can_view_own_sanctions(client, student_headers):
    r = client.get("/api/sanctions/students/me", headers=student_headers)
    assert r.status_code == 200


def test_student_cannot_manage_sanctions(client, student_headers):
    r = client.put("/api/sanctions/events/999/config", headers=student_headers, json={
        "sanctions_enabled": True,
    })
    assert r.status_code == 403

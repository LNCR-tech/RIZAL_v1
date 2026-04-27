def test_get_face_status(client, campus_admin_headers):
    r = client.get("/api/auth/security/face-status", headers=campus_admin_headers)
    assert r.status_code == 200


def test_list_sessions(client, campus_admin_headers):
    r = client.get("/api/auth/security/sessions", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_security_requires_auth(client):
    r = client.get("/api/auth/security/face-status")
    assert r.status_code == 401

def test_get_governance_access_me(client, campus_admin_headers):
    r = client.get("/api/governance/access/me", headers=campus_admin_headers)
    assert r.status_code == 200


def test_get_governance_settings(client, campus_admin_headers):
    r = client.get("/api/governance/settings/me", headers=campus_admin_headers)
    assert r.status_code == 200


def test_student_governance_access(client, student_headers):
    r = client.get("/api/governance/access/me", headers=student_headers)
    assert r.status_code == 200
    data = r.json()
    assert data.get("permission_codes") == [] or isinstance(data.get("permission_codes"), list)


def test_governance_requires_auth(client):
    r = client.get("/api/governance/access/me")
    assert r.status_code == 401

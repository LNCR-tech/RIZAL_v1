def test_get_school(client, campus_admin_headers):
    r = client.get("/api/school/me", headers=campus_admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data


def test_update_school_branding(client, campus_admin_headers):
    r = client.patch("/api/school/me/branding", headers=campus_admin_headers, json={
        "primary_color": "#FF0000"
    })
    assert r.status_code == 200


def test_student_cannot_update_school(client, student_headers):
    r = client.patch("/api/school/me/branding", headers=student_headers, json={
        "primary_color": "#FF0000"
    })
    assert r.status_code == 403


def test_get_school_audit_logs(client, campus_admin_headers):
    r = client.get("/api/audit-logs/", headers=campus_admin_headers)
    assert r.status_code == 200

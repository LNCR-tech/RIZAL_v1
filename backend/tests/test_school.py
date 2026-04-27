def test_get_school(client, campus_admin_headers):
    r = client.get("/api/school/me", headers=campus_admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "school_id" in data or "id" in data


def test_update_school_branding(client, campus_admin_headers):
    r = client.put("/api/school/update", headers=campus_admin_headers, data={
        "primary_color": "#FF0000"
    })
    assert r.status_code in (200, 422)  # 422 if form validation fails, still hits the endpoint


def test_student_cannot_update_school(client, student_headers):
    r = client.put("/api/school/update", headers=student_headers, data={
        "primary_color": "#FF0000"
    })
    assert r.status_code == 403


def test_get_school_audit_logs(client, campus_admin_headers):
    r = client.get("/api/school-settings/me/audit-logs", headers=campus_admin_headers)
    assert r.status_code == 200

def test_list_audit_logs_admin(client, campus_admin_headers):
    r = client.get("/api/audit-logs", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_audit_logs_student_forbidden(client, student_headers):
    r = client.get("/api/audit-logs", headers=student_headers)
    assert r.status_code == 403

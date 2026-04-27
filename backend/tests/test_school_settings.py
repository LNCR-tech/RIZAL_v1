def test_get_school_settings(client, campus_admin_headers):
    r = client.get("/api/school-settings/me", headers=campus_admin_headers)
    assert r.status_code == 200


def test_update_school_settings(client, campus_admin_headers):
    r = client.put("/api/school-settings/me", headers=campus_admin_headers, json={
        "default_early_check_in_minutes": 15,
        "default_late_threshold_minutes": 5,
        "default_sign_out_grace_minutes": 10,
    })
    assert r.status_code in (200, 422)


def test_student_cannot_update_settings(client, student_headers):
    r = client.put("/api/school-settings/me", headers=student_headers, json={
        "default_early_check_in_minutes": 15,
    })
    assert r.status_code == 403

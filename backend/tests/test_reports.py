def test_school_attendance_summary(client, campus_admin_headers):
    r = client.get("/api/attendance/summary", headers=campus_admin_headers)
    assert r.status_code == 200


def test_student_overview(client, campus_admin_headers):
    r = client.get("/api/attendance/students/overview", headers=campus_admin_headers)
    assert r.status_code == 200


def test_student_attendance_stats(client, campus_admin_headers, db_session):
    from app.models.user import StudentProfile
    profile = db_session.query(StudentProfile).filter_by(student_number="STU-001").first()
    r = client.get(f"/api/attendance/students/{profile.id}/stats", headers=campus_admin_headers)
    assert r.status_code == 200


def test_reports_require_auth(client):
    r = client.get("/api/attendance/summary")
    assert r.status_code == 401

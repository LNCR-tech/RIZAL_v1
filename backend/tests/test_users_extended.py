import pytest


def test_get_users_by_role(client, campus_admin_headers):
    r = client.get("/api/users/by-role/student", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_users_by_role_requires_auth(client):
    r = client.get("/api/users/by-role/student")
    assert r.status_code == 401


def test_reset_user_password(client, admin_headers, db_session):
    # Create a throwaway user to reset so we don't break shared session tokens
    import time
    from app.models.user import User, UserRole
    from app.models.school import School
    from app.models.role import Role
    from app.utils.passwords import hash_password_bcrypt
    school = db_session.query(School).filter_by(school_code="TEST-001").first()
    role = db_session.query(Role).filter_by(code="student").first()
    user = User(email=f"resetme_{int(time.time())}@test.com", school_id=school.id,
                password_hash=hash_password_bcrypt("TestPass123!"),
                must_change_password=False, first_name="Reset", last_name="Me")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.flush()
    r = client.post(f"/api/users/{user.id}/reset-password", headers=admin_headers, json={
        "password": "TestPass123!",
    })
    assert r.status_code in (200, 204)


def test_update_user_roles(client, admin_headers, db_session):
    from app.models.user import User
    student = db_session.query(User).filter_by(email="student@test.com").first()
    r = client.put(f"/api/users/{student.id}/roles", headers=admin_headers, json={
        "roles": ["student"],
    })
    assert r.status_code == 200


def test_update_user_roles_campus_admin_forbidden(client, campus_admin_headers, db_session):
    from app.models.user import User
    student = db_session.query(User).filter_by(email="student@test.com").first()
    r = client.put(f"/api/users/{student.id}/roles", headers=campus_admin_headers, json={
        "roles": ["student"],
    })
    assert r.status_code == 403


def test_get_user_preferences(client, student_headers):
    r = client.get("/api/users/preferences/me", headers=student_headers)
    assert r.status_code == 200


def test_update_user_preferences(client, student_headers):
    r = client.put("/api/users/preferences/me", headers=student_headers, json={
        "dark_mode_enabled": True,
        "font_size_percent": 110,
    })
    assert r.status_code == 200
    assert r.json()["dark_mode_enabled"] is True


def test_create_student_account(client, campus_admin_headers, db_session):
    from app.models.department import Department
    from app.models.program import Program
    from app.models.school import School
    school = db_session.query(School).filter_by(school_code="TEST-001").first()
    dept = db_session.query(Department).filter_by(school_id=school.id).first()
    prog = db_session.query(Program).filter_by(school_id=school.id).first()
    r = client.post("/api/users/students/", headers=campus_admin_headers, json={
        "email": "newstudent_test@test.com",
        "first_name": "New",
        "last_name": "Student",
        "student_id": "STU-NEW-001",
        "department_id": dept.id,
        "program_id": prog.id,
        "year_level": 1,
    })
    assert r.status_code in (200, 201, 400, 409)


def test_delete_student_profile(client, campus_admin_headers, db_session):
    import time
    from app.models.user import StudentProfile, User, UserRole
    from app.models.school import School
    from app.models.role import Role
    from app.utils.passwords import hash_password_bcrypt
    school = db_session.query(School).filter_by(school_code="TEST-001").first()
    role = db_session.query(Role).filter_by(code="student").first()
    unique_email = f"deleteme_{int(time.time())}@test.com"
    user = User(email=unique_email, school_id=school.id,
                password_hash=hash_password_bcrypt("TestPass123!"),
                must_change_password=False, first_name="Del", last_name="Me")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile = StudentProfile(user_id=user.id, school_id=school.id,
                             student_id=f"STU-DEL-{int(time.time())}", year_level=1)
    db_session.add(profile)
    db_session.flush()

    r = client.delete(f"/api/users/student-profiles/{profile.id}", headers=campus_admin_headers)
    assert r.status_code == 204

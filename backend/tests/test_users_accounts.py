"""Tests for untested user account endpoints: get by ID, delete, get by role."""
import time
import pytest
from app.models.user import User, UserRole
from app.models.school import School
from app.models.role import Role
from app.utils.passwords import hash_password_bcrypt


def _make_user(db, school, role, suffix=None):
    tag = suffix or int(time.time() * 1000)
    user = User(
        email=f"tmpuser_{tag}@test.com",
        school_id=school.id,
        password_hash=hash_password_bcrypt("TestPass123!"),
        must_change_password=False,
        first_name="Tmp",
        last_name="User",
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    return user


def test_get_user_by_id_self(client, student_headers, db_session):
    student = db_session.query(User).filter_by(email="student@test.com").first()
    r = client.get(f"/api/users/{student.id}", headers=student_headers)
    assert r.status_code == 200
    assert r.json()["id"] == student.id


def test_get_user_by_id_admin(client, campus_admin_headers, db_session):
    student = db_session.query(User).filter_by(email="student@test.com").first()
    r = client.get(f"/api/users/{student.id}", headers=campus_admin_headers)
    assert r.status_code == 200


def test_get_user_by_id_forbidden_cross_user(client, student_headers, db_session):
    campus_admin = db_session.query(User).filter_by(email="campus_admin@test.com").first()
    r = client.get(f"/api/users/{campus_admin.id}", headers=student_headers)
    assert r.status_code == 403


def test_get_user_by_id_not_found(client, campus_admin_headers):
    r = client.get("/api/users/999999", headers=campus_admin_headers)
    assert r.status_code == 404


def test_get_users_by_role_teacher(client, campus_admin_headers):
    r = client.get("/api/users/by-role/teacher", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_users_by_role_student(client, campus_admin_headers):
    r = client.get("/api/users/by-role/student", headers=campus_admin_headers)
    assert r.status_code == 200
    users = r.json()
    assert all(
        any("student" in ur["role"]["name"].lower() for ur in u.get("roles", []))
        for u in users
    )


def test_delete_user(client, campus_admin_headers, db_session):
    school = db_session.query(School).filter_by(school_code="TEST-001").first()
    role = db_session.query(Role).filter_by(code="student").first()
    user = _make_user(db_session, school, role)
    r = client.delete(f"/api/users/{user.id}", headers=campus_admin_headers)
    assert r.status_code == 204


def test_delete_user_not_found(client, campus_admin_headers):
    r = client.delete("/api/users/999999", headers=campus_admin_headers)
    assert r.status_code == 404


def test_delete_user_requires_auth(client, db_session):
    student = db_session.query(User).filter_by(email="student@test.com").first()
    r = client.delete(f"/api/users/{student.id}")
    assert r.status_code == 401

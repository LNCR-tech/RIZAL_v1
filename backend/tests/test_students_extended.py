import pytest
import time
from app.models.user import StudentProfile

def test_create_student_with_valid_year_level_and_status(client, campus_admin_headers, db_session):
    unique_id = int(time.time() * 1000)
    user_payload = {
        "email": f"newstudent_yearlevel_{unique_id}@test.com",
        "first_name": "Year",
        "last_name": "Level",
        "roles": ["student"]
    }
    r = client.post("/api/users/", json=user_payload, headers=campus_admin_headers)
    assert r.status_code == 200
    user_id = r.json()["id"]

    # Now create student profile
    # We need a valid department and program for the test school. Let's fetch one.
    deps = client.get("/api/departments/", headers=campus_admin_headers).json()
    progs = client.get("/api/programs/", headers=campus_admin_headers).json()

    profile_payload = {
        "user_id": user_id,
        "student_id": f"YL-{unique_id}",
        "department_id": deps[0]["id"],
        "program_id": progs[0]["id"],
        "year_level": 3,
        "student_status": "ACTIVE",
        "promotion_locked": True
    }
    r = client.post("/api/users/admin/students/", json=profile_payload, headers=campus_admin_headers)
    assert r.status_code == 200
    assert r.json()["student_profile"]["year_level"] == 3
    assert r.json()["student_profile"]["student_status"] == "ACTIVE"
    assert r.json()["student_profile"]["promotion_locked"] is True

def test_invalid_year_level(client, campus_admin_headers, db_session):
    profile_payload = {
        "user_id": 9999,
        "student_id": "YL-2026-002",
        "department_id": 1,
        "program_id": 1,
        "year_level": 6, # Invalid, > 5
    }
    r = client.post("/api/users/admin/students/", json=profile_payload, headers=campus_admin_headers)
    assert r.status_code == 422 # Pydantic validation error

def test_invalid_student_status(client, campus_admin_headers, db_session):
    profile_payload = {
        "user_id": 9999,
        "student_id": "YL-2026-003",
        "department_id": 1,
        "program_id": 1,
        "year_level": 1,
        "student_status": "INVALID_STATUS"
    }
    r = client.post("/api/users/admin/students/", json=profile_payload, headers=campus_admin_headers)
    assert r.status_code == 422 # Pydantic validation error

def test_default_active_status(client, campus_admin_headers, db_session):
    unique_id = int(time.time() * 1000)
    user_payload = {
        "email": f"newstudent_defaultstatus_{unique_id}@test.com",
        "first_name": "Default",
        "last_name": "Status",
        "roles": ["student"]
    }
    r = client.post("/api/users/", json=user_payload, headers=campus_admin_headers)
    assert r.status_code == 200
    user_id = r.json()["id"]

    deps = client.get("/api/departments/", headers=campus_admin_headers).json()
    progs = client.get("/api/programs/", headers=campus_admin_headers).json()

    profile_payload = {
        "user_id": user_id,
        "student_id": f"YD-{unique_id}",
        "department_id": deps[0]["id"],
        "program_id": progs[0]["id"]
    }
    r = client.post("/api/users/admin/students/", json=profile_payload, headers=campus_admin_headers)
    assert r.status_code == 200
    assert r.json()["student_profile"]["year_level"] == 1 # Default
    assert r.json()["student_profile"]["student_status"] == "ACTIVE" # Default
    assert r.json()["student_profile"]["promotion_locked"] is False # Default


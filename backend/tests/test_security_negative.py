import pytest
from uuid import uuid4

from app.utils.passwords import verify_password_bcrypt


def test_wrong_password_rejected(client):
    r = client.post("/login", json={"email": "admin@test.com", "password": "WrongPassword!"})
    assert r.status_code in [401, 404, 422], "Should fail auth or validation"

def test_expired_or_tampered_token_rejected(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}123"} # Tampered
    r = client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 401

def test_sql_injection_attempt_rejected(client):
    payload = {"email": "admin@test.com' OR '1'='1", "password": "Password"}
    r = client.post("/login", json=payload)
    assert r.status_code in [401, 404, 422], "Should fail auth or validation, not 500"

def test_xss_payload_rejection(client, campus_admin_headers):
    payload = {"name": "<script>alert(1)</script>", "description": "Test", "start_date": "2024-01-01", "end_date": "2024-01-02", "school_id": 1}
    r = client.post("/api/v1/events/", headers=campus_admin_headers, json=payload)
    assert r.status_code in [400, 422, 200]
    
    if r.status_code == 200:
        assert "<script>" not in r.json()["name"], "Payload should be sanitized if accepted"

def test_cross_school_data_access_blocked(client, campus_admin_headers, db_session):
    from app.models.school import School

    unique = uuid4().hex[:12].upper()
    school_code = f"TEST-{unique}"
    other_school = School(
        school_code=school_code,
        legal_name=f"Other {unique}",
        display_name=f"Other {unique}",
        address="None",
        is_active=True,
    )
    db_session.add(other_school)
    db_session.commit()
    db_session.refresh(other_school)
    
    try:
        r = client.get(f"/api/school/admin/{other_school.id}/status", headers=campus_admin_headers)
        assert r.status_code in [403, 404], "Campus admin should not access other schools"
    finally:
        db_session.rollback()
        school = db_session.query(School).filter_by(school_code=school_code).first()
        if school is not None:
            db_session.delete(school)
            db_session.commit()

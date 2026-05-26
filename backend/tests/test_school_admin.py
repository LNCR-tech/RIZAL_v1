from uuid import uuid4

from app.models.school import School
from app.models.user import User


def _cleanup_created_school(db_session, *, school_code: str, school_it_email: str) -> None:
    db_session.rollback()

    school_it_user = db_session.query(User).filter_by(email=school_it_email).first()
    if school_it_user is not None:
        db_session.delete(school_it_user)
        db_session.flush()

    school = db_session.query(School).filter_by(school_code=school_code).first()
    if school is not None:
        db_session.delete(school)

    db_session.commit()


def test_admin_list_schools(client, admin_headers):
    r = client.get("/api/school/admin/list", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_list_school_it_accounts(client, admin_headers):
    r = client.get("/api/school/admin/school-it-accounts", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_list_schools_requires_admin(client, campus_admin_headers):
    r = client.get("/api/school/admin/list", headers=campus_admin_headers)
    assert r.status_code == 403


def test_admin_list_schools_requires_auth(client):
    r = client.get("/api/school/admin/list")
    assert r.status_code == 401


def test_admin_create_school_with_school_it(client, admin_headers, db_session):
    unique = uuid4().hex[:12].upper()
    school_code = f"TEST-{unique}"
    school_name = f"New Test School {unique}"
    school_it_email = f"newschoolit-{unique.lower()}@test.com"

    r = client.post("/api/school/admin/create-school-it", data={
        "school_name": school_name,
        "school_code": school_code,
        "primary_color": "#123456",
        "school_it_email": school_it_email,
        "school_it_first_name": "New",
        "school_it_last_name": "SchoolIT",
        "school_it_password": "TestPass123!",
    })
    # Requires admin auth
    assert r.status_code == 401

    try:
        r = client.post("/api/school/admin/create-school-it", headers=admin_headers, data={
            "school_name": school_name,
            "school_code": school_code,
            "primary_color": "#123456",
            "school_it_email": school_it_email,
            "school_it_first_name": "New",
            "school_it_last_name": "SchoolIT",
            "school_it_password": "TestPass123!",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["school"]["school_code"] == school_code
        assert data["school_it_email"] == school_it_email
    finally:
        _cleanup_created_school(
            db_session,
            school_code=school_code,
            school_it_email=school_it_email,
        )

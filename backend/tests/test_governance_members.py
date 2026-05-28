import pytest


@pytest.fixture(scope="module")
def ssg_unit_id(client, campus_admin_headers):
    r = client.get("/api/governance/units", headers=campus_admin_headers, params={"unit_type": "SSG"})
    if r.status_code == 200 and r.json():
        return r.json()[0]["id"]
    r = client.post("/api/governance/units", headers=campus_admin_headers, json={
        "unit_code": "SSG-TEST", "unit_name": "Test SSG", "unit_type": "SSG",
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


@pytest.fixture()
def isolated_governance_units(db_session):
    import uuid

    from app.models.governance_hierarchy import GovernanceMember, GovernanceUnit
    from app.models.user import StudentProfile, User

    campus_admin = db_session.query(User).filter_by(email="campus_admin@test.com").one()
    student = db_session.query(User).filter_by(email="student_year2@test.com").one()
    replacement_student = db_session.query(User).filter_by(email="student_year5@test.com").one()
    student_profile = db_session.query(StudentProfile).filter_by(user_id=student.id).one()

    db_session.query(GovernanceMember).filter(
        GovernanceMember.user_id.in_([student.id, replacement_student.id])
    ).delete(synchronize_session=False)

    suffix = uuid.uuid4().hex[:8].upper()
    ssg_unit = GovernanceUnit(
        school_id=campus_admin.school_id,
        unit_code=f"TSSG-{suffix}",
        unit_name=f"Test SSG {suffix}",
        unit_type="SSG",
        created_by_user_id=campus_admin.id,
        is_active=True,
    )
    sg_unit = GovernanceUnit(
        school_id=campus_admin.school_id,
        unit_code=f"TSG-{suffix}",
        unit_name=f"Test SG {suffix}",
        unit_type="SG",
        department_id=student_profile.department_id,
        created_by_user_id=campus_admin.id,
        is_active=True,
    )
    db_session.add_all([ssg_unit, sg_unit])
    db_session.flush()
    sg_unit.parent_unit_id = ssg_unit.id
    db_session.commit()

    try:
        yield ssg_unit, sg_unit, student, replacement_student
    finally:
        unit_ids = [ssg_unit.id, sg_unit.id]
        user_ids = [student.id, replacement_student.id]
        db_session.query(GovernanceMember).filter(
            (GovernanceMember.governance_unit_id.in_(unit_ids))
            | (GovernanceMember.user_id.in_(user_ids))
        ).delete(synchronize_session=False)
        db_session.query(GovernanceUnit).filter(GovernanceUnit.id.in_(unit_ids)).delete(synchronize_session=False)
        db_session.commit()


def test_get_ssg_setup(client, campus_admin_headers):
    r = client.get("/api/governance/ssg/setup", headers=campus_admin_headers)
    assert r.status_code in (200, 404)


def test_search_governance_students(client, campus_admin_headers):
    r = client.get("/api/governance/students/search", headers=campus_admin_headers, params={"q": "test"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_governance_students(client, campus_admin_headers):
    r = client.get("/api/governance/students", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_assign_and_update_and_delete_member(client, campus_admin_headers, db_session, ssg_unit_id):
    from app.models.user import User
    student = db_session.query(User).filter_by(email="student@test.com").first()

    r = client.post(f"/api/governance/units/{ssg_unit_id}/members", headers=campus_admin_headers, json={
        "user_id": student.id, "position_title": "Officer",
    })
    assert r.status_code in (200, 201), r.text
    member_id = r.json()["id"]

    r = client.patch(f"/api/governance/members/{member_id}", headers=campus_admin_headers, json={
        "position_title": "President",
    })
    assert r.status_code == 200

    r = client.delete(f"/api/governance/members/{member_id}", headers=campus_admin_headers)
    assert r.status_code == 204


def test_create_list_update_delete_announcement(client, campus_admin_headers, ssg_unit_id):
    r = client.post(f"/api/governance/units/{ssg_unit_id}/announcements", headers=campus_admin_headers, json={
        "title": "Test Announcement", "body": "Hello world", "status": "draft",
    })
    assert r.status_code in (200, 201), r.text
    ann_id = r.json()["id"]

    r = client.get(f"/api/governance/units/{ssg_unit_id}/announcements", headers=campus_admin_headers)
    assert r.status_code == 200
    assert any(a["id"] == ann_id for a in r.json())

    r = client.patch(f"/api/governance/announcements/{ann_id}", headers=campus_admin_headers, json={
        "title": "Updated",
    })
    assert r.status_code == 200

    r = client.delete(f"/api/governance/announcements/{ann_id}", headers=campus_admin_headers)
    assert r.status_code == 204


def test_announcements_monitor(client, campus_admin_headers):
    r = client.get("/api/governance/announcements/monitor", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_student_cannot_access_announcements_monitor(client, student_headers):
    r = client.get("/api/governance/announcements/monitor", headers=student_headers)
    assert r.status_code == 403


def test_assign_member_rejects_user_active_in_another_governance_unit(
    client,
    campus_admin_headers,
    isolated_governance_units,
):
    ssg_unit, sg_unit, student, _ = isolated_governance_units

    r = client.post(
        f"/api/governance/units/{ssg_unit.id}/members",
        headers=campus_admin_headers,
        json={"user_id": student.id, "position_title": "Officer"},
    )
    assert r.status_code == 201, r.text

    r = client.post(
        f"/api/governance/units/{sg_unit.id}/members",
        headers=campus_admin_headers,
        json={"user_id": student.id, "position_title": "Officer"},
    )
    assert r.status_code == 409
    assert "one governance unit" in r.json()["detail"]


def test_search_candidates_excludes_user_active_in_another_governance_unit(
    client,
    campus_admin_headers,
    isolated_governance_units,
):
    ssg_unit, sg_unit, student, _ = isolated_governance_units

    r = client.post(
        f"/api/governance/units/{ssg_unit.id}/members",
        headers=campus_admin_headers,
        json={"user_id": student.id, "position_title": "Officer"},
    )
    assert r.status_code == 201, r.text

    r = client.get(
        "/api/governance/students/search",
        headers=campus_admin_headers,
        params={"q": "student_year2", "governance_unit_id": sg_unit.id},
    )
    assert r.status_code == 200, r.text
    assert all(candidate["user"]["id"] != student.id for candidate in r.json())


def test_update_member_rejects_user_active_in_another_governance_unit(
    client,
    campus_admin_headers,
    isolated_governance_units,
):
    ssg_unit, sg_unit, student, replacement_student = isolated_governance_units

    r = client.post(
        f"/api/governance/units/{ssg_unit.id}/members",
        headers=campus_admin_headers,
        json={"user_id": student.id, "position_title": "Officer"},
    )
    assert r.status_code == 201, r.text

    r = client.post(
        f"/api/governance/units/{sg_unit.id}/members",
        headers=campus_admin_headers,
        json={"user_id": replacement_student.id, "position_title": "Officer"},
    )
    assert r.status_code == 201, r.text
    member_id = r.json()["id"]

    r = client.patch(
        f"/api/governance/members/{member_id}",
        headers=campus_admin_headers,
        json={"user_id": student.id},
    )
    assert r.status_code == 409
    assert "one governance unit" in r.json()["detail"]

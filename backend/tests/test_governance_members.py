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

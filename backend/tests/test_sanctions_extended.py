import pytest


@pytest.fixture(scope="module")
def event_id(db_session):
    from app.models.event import Event
    event = db_session.query(Event).first()
    if event is None:
        pytest.skip("No events in test DB")
    return event.id


def test_get_sanction_config(client, campus_admin_headers, event_id):
    r = client.get(f"/api/sanctions/events/{event_id}/config", headers=campus_admin_headers)
    assert r.status_code in (200, 404)


def test_put_sanction_config(client, campus_admin_headers, event_id):
    r = client.put(f"/api/sanctions/events/{event_id}/config", headers=campus_admin_headers, json={
        "sanctions_enabled": False,
        "item_definitions": [],
    })
    assert r.status_code in (200, 404, 422)


def test_get_sanction_students(client, campus_admin_headers, event_id):
    r = client.get(f"/api/sanctions/events/{event_id}/students", headers=campus_admin_headers)
    assert r.status_code in (200, 404)


def test_get_sanction_delegation(client, campus_admin_headers, event_id):
    r = client.get(f"/api/sanctions/events/{event_id}/delegation", headers=campus_admin_headers)
    assert r.status_code in (200, 404)


def test_get_sanctions_dashboard(client, campus_admin_headers):
    r = client.get("/api/sanctions/dashboard", headers=campus_admin_headers)
    assert r.status_code == 200


def test_get_my_sanctions(client, student_headers):
    r = client.get("/api/sanctions/students/me", headers=student_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_clearance_deadline(client, campus_admin_headers):
    r = client.get("/api/sanctions/clearance-deadline", headers=campus_admin_headers)
    assert r.status_code in (200, 404)


def test_sanctions_require_auth(client, event_id):
    r = client.get(f"/api/sanctions/events/{event_id}/config")
    assert r.status_code == 401


def test_student_sanctions_detail(client, campus_admin_headers, db_session):
    from app.models.user import User
    student = db_session.query(User).filter_by(email="student@test.com").first()
    r = client.get(f"/api/sanctions/students/{student.id}", headers=campus_admin_headers)
    assert r.status_code in (200, 404)


def test_sanction_export_requires_auth(client, event_id):
    r = client.get(f"/api/sanctions/events/{event_id}/export")
    assert r.status_code == 401

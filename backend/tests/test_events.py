import pytest


EVENT_PAYLOAD = {
    "name": "Test Event",
    "start_datetime": "2099-01-01T08:00:00+00:00",
    "end_datetime": "2099-01-01T17:00:00+00:00",
    "location": "Test Hall",
}


@pytest.fixture(scope="module")
def event_id(client, campus_admin_headers):
    r = client.post("/api/events/", headers=campus_admin_headers, json=EVENT_PAYLOAD)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_list_events(client, campus_admin_headers):
    r = client.get("/api/events/", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_event(client, campus_admin_headers, event_id):
    r = client.get(f"/api/events/{event_id}", headers=campus_admin_headers)
    assert r.status_code == 200
    assert r.json()["id"] == event_id


def test_update_event(client, campus_admin_headers, event_id):
    r = client.patch(f"/api/events/{event_id}", headers=campus_admin_headers, json={"name": "Updated Event"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Event"


def test_student_cannot_create_event(client, student_headers):
    r = client.post("/api/events/", headers=student_headers, json=EVENT_PAYLOAD)
    assert r.status_code == 403


def test_delete_event(client, campus_admin_headers, event_id):
    r = client.delete(f"/api/events/{event_id}", headers=campus_admin_headers)
    assert r.status_code in (200, 204)

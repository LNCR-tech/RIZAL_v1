import pytest
from datetime import datetime

from app.core.timezones import PHILIPPINE_TIMEZONE
from app.models.event import Event as EventModel


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


def test_create_event_with_naive_local_datetime_is_normalized(client, campus_admin_headers, db_session):
    payload = {
        "name": "Naive Local Event",
        "start_datetime": "2099-01-03T08:15:00",
        "end_datetime": "2099-01-03T10:45:00",
        "location": "Timezone Hall",
    }

    response = client.post("/api/events/", headers=campus_admin_headers, json=payload)
    assert response.status_code in (200, 201), response.text
    body = response.json()

    start_value = datetime.fromisoformat(body["start_datetime"].replace("Z", "+00:00"))
    end_value = datetime.fromisoformat(body["end_datetime"].replace("Z", "+00:00"))

    assert start_value.tzinfo is not None
    assert end_value.tzinfo is not None

    start_local = start_value.astimezone(PHILIPPINE_TIMEZONE)
    end_local = end_value.astimezone(PHILIPPINE_TIMEZONE)
    assert (start_local.year, start_local.month, start_local.day, start_local.hour, start_local.minute) == (2099, 1, 3, 8, 15)
    assert (end_local.year, end_local.month, end_local.day, end_local.hour, end_local.minute) == (2099, 1, 3, 10, 45)

    stored_event = db_session.query(EventModel).filter(EventModel.id == body["id"]).first()
    assert stored_event is not None

    stored_start_local = stored_event.start_datetime.astimezone(PHILIPPINE_TIMEZONE)
    stored_end_local = stored_event.end_datetime.astimezone(PHILIPPINE_TIMEZONE)
    assert (stored_start_local.year, stored_start_local.month, stored_start_local.day, stored_start_local.hour, stored_start_local.minute) == (2099, 1, 3, 8, 15)
    assert (stored_end_local.year, stored_end_local.month, stored_end_local.day, stored_end_local.hour, stored_end_local.minute) == (2099, 1, 3, 10, 45)

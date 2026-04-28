import pytest


@pytest.fixture(scope="module")
def event_id(db_session):
    from app.models.event import Event
    event = db_session.query(Event).first()
    if event is None:
        pytest.skip("No events in test DB")
    return event.id


def test_get_ongoing_events(client, campus_admin_headers):
    r = client.get("/api/events/ongoing", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_event_attendees(client, campus_admin_headers, event_id):
    r = client.get(f"/api/events/{event_id}/attendees", headers=campus_admin_headers)
    assert r.status_code == 200


def test_get_event_stats(client, campus_admin_headers, event_id):
    r = client.get(f"/api/events/{event_id}/stats", headers=campus_admin_headers)
    assert r.status_code == 200


def test_get_event_time_status(client, campus_admin_headers, event_id):
    r = client.get(f"/api/events/{event_id}/time-status", headers=campus_admin_headers)
    assert r.status_code == 200


def test_verify_event_location(client, campus_admin_headers, event_id):
    r = client.post(f"/api/events/{event_id}/verify-location", headers=campus_admin_headers, json={
        "latitude": 14.5995, "longitude": 120.9842, "accuracy_m": 10.0,
    })
    assert r.status_code in (200, 400, 403, 409)


def test_update_event_status_requires_auth(client, event_id):
    r = client.patch(f"/api/events/{event_id}/status", json={"status": "cancelled"})
    assert r.status_code == 401


def test_open_sign_out_early_requires_auth(client, event_id):
    r = client.post(f"/api/events/{event_id}/sign-out/open-early",
                    json={"use_sign_out_grace_minutes": True})
    assert r.status_code == 401


def test_ongoing_events_requires_auth(client):
    r = client.get("/api/events/ongoing")
    assert r.status_code == 401

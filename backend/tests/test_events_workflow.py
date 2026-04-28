"""Tests for untested event endpoints: attendees, stats, status patch, sign-out-early."""
import pytest
from datetime import datetime, timedelta, timezone


@pytest.fixture(scope="module")
def workflow_event_id(client, campus_admin_headers):
    now = datetime.now(timezone.utc)
    r = client.post("/api/events/", headers=campus_admin_headers, json={
        "name": "Workflow Test Event",
        "start_datetime": (now + timedelta(hours=1)).isoformat(),
        "end_datetime": (now + timedelta(hours=3)).isoformat(),
        "location": "Test Hall",
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


@pytest.fixture(scope="module")
def completed_event_id(client, campus_admin_headers):
    now = datetime.now(timezone.utc)
    r = client.post("/api/events/", headers=campus_admin_headers, json={
        "name": "Completed Test Event",
        "start_datetime": (now - timedelta(hours=3)).isoformat(),
        "end_datetime": (now - timedelta(hours=1)).isoformat(),
        "location": "Test Hall",
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_get_event_attendees(client, campus_admin_headers, workflow_event_id):
    r = client.get(f"/api/events/{workflow_event_id}/attendees", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_event_attendees_requires_auth(client, workflow_event_id):
    r = client.get(f"/api/events/{workflow_event_id}/attendees")
    assert r.status_code == 401


def test_get_event_attendees_not_found(client, campus_admin_headers):
    r = client.get("/api/events/999999/attendees", headers=campus_admin_headers)
    assert r.status_code == 404


def test_get_event_stats(client, campus_admin_headers, workflow_event_id):
    r = client.get(f"/api/events/{workflow_event_id}/stats", headers=campus_admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "statuses" in data


def test_get_event_stats_requires_auth(client, workflow_event_id):
    r = client.get(f"/api/events/{workflow_event_id}/stats")
    assert r.status_code == 401


def test_get_event_stats_not_found(client, campus_admin_headers):
    r = client.get("/api/events/999999/stats", headers=campus_admin_headers)
    assert r.status_code == 404


def test_patch_event_status_cancel(client, campus_admin_headers, workflow_event_id):
    r = client.patch(
        f"/api/events/{workflow_event_id}/status",
        headers=campus_admin_headers,
        json={"status": "cancelled"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


def test_patch_event_status_requires_auth(client, workflow_event_id):
    r = client.patch(f"/api/events/{workflow_event_id}/status", json={"status": "cancelled"})
    assert r.status_code == 401


def test_patch_event_status_not_found(client, campus_admin_headers):
    r = client.patch("/api/events/999999/status", headers=campus_admin_headers, json={"status": "cancelled"})
    assert r.status_code == 404


def test_sign_out_open_early_not_started(client, campus_admin_headers):
    """Event that hasn't started yet should reject early sign-out."""
    now = datetime.now(timezone.utc)
    r = client.post("/api/events/", headers=campus_admin_headers, json={
        "name": "Future Event",
        "start_datetime": (now + timedelta(hours=2)).isoformat(),
        "end_datetime": (now + timedelta(hours=4)).isoformat(),
        "location": "Test Hall",
    })
    assert r.status_code in (200, 201)
    eid = r.json()["id"]
    r2 = client.post(
        f"/api/events/{eid}/sign-out/open-early",
        headers=campus_admin_headers,
        json={"use_sign_out_grace_minutes": True},
    )
    assert r2.status_code == 409


def test_sign_out_open_early_not_found(client, campus_admin_headers):
    r = client.post(
        "/api/events/999999/sign-out/open-early",
        headers=campus_admin_headers,
        json={"use_sign_out_grace_minutes": True},
    )
    assert r.status_code == 404


def test_sign_out_open_early_requires_auth(client, workflow_event_id):
    r = client.post(
        f"/api/events/{workflow_event_id}/sign-out/open-early",
        json={"use_sign_out_grace_minutes": True},
    )
    assert r.status_code == 401

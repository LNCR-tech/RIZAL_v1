import pytest
from app.schemas.user import User
from app.schemas.event import Event

def test_token_response_shape(client, admin_token):
    # Ensure login returns correct schema
    r = client.post("/login", json={"email": "admin@test.com", "password": "TestPass123!"})
    data = r.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    
def test_users_me_shape(client, admin_headers):
    r = client.get("/api/v1/users/me", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "email" in data
    assert "first_name" in data
    assert "roles" in data
    assert isinstance(data["roles"], list)

def test_events_list_schema(client, campus_admin_headers):
    r = client.get("/api/v1/events/", headers=campus_admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data or isinstance(data, list)
    items = data["items"] if "items" in data else data
    if items:
        event = items[0]
        assert "id" in event
        assert "name" in event
        # Assuming the returned format maps to the database or schema aliasing, test presence.
        # EventBase uses start_datetime, but the model has start_at. Let's check the API response shape.
        has_start = "start_date" in event or "start_datetime" in event or "start_at" in event
        assert has_start, "Event response missing a recognizable start time field"

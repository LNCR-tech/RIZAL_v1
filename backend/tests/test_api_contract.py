import pytest
from app.schemas.user import UserResponse
from app.schemas.events import EventResponse

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
        assert "start_date" in event
        # Verify date format is string (ISO)
        assert isinstance(event["start_date"], str)

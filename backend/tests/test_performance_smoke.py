import pytest
import time

def test_login_performance_target(client):
    start = time.perf_counter()
    r = client.post("/login", json={"email": "student@test.com", "password": "TestPass123!"})
    duration = time.perf_counter() - start
    
    assert r.status_code == 200
    assert duration < 1.5, f"Login endpoint took {duration}s, target < 1.5s"

def test_me_endpoint_performance(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    start = time.perf_counter()
    r = client.get("/api/v1/users/me", headers=headers)
    duration = time.perf_counter() - start
    
    assert r.status_code == 200
    assert duration < 0.5, f"/me endpoint took {duration}s, target < 0.5s"

def test_events_list_performance(client, campus_admin_headers):
    start = time.perf_counter()
    r = client.get("/api/v1/events/", headers=campus_admin_headers)
    duration = time.perf_counter() - start
    
    assert r.status_code == 200
    assert duration < 1.0, f"Events list took {duration}s, target < 1.0s"

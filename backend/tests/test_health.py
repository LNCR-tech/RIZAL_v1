def test_health(client):
    r = client.get("/health")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "status" in data
    assert data["database"]["ok"] is True

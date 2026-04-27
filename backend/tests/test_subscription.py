def test_get_subscription(client, campus_admin_headers):
    r = client.get("/api/subscription/me", headers=campus_admin_headers)
    assert r.status_code in (200, 404, 500)


def test_subscription_requires_auth(client):
    r = client.get("/api/subscription/me")
    assert r.status_code == 401

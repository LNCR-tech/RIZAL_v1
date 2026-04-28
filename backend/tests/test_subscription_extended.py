def test_update_subscription(client, campus_admin_headers):
    r = client.put("/api/subscription/me", headers=campus_admin_headers, json={
        "auto_renew": False,
        "reminder_days_before": 7,
    })
    assert r.status_code == 200


def test_run_subscription_reminders(client, campus_admin_headers):
    r = client.post("/api/subscription/run-reminders", headers=campus_admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "schools_checked" in data


def test_subscription_requires_auth(client):
    r = client.put("/api/subscription/me", json={})
    assert r.status_code == 401

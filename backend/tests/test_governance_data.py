def test_create_and_list_data_requests(client, campus_admin_headers):
    r = client.post("/api/governance/requests", headers=campus_admin_headers, json={
        "request_type": "export", "reason": "Test export request",
    })
    assert r.status_code == 200, r.text
    req_id = r.json()["id"]

    r = client.get("/api/governance/requests", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r = client.patch(f"/api/governance/requests/{req_id}", headers=campus_admin_headers, json={
        "status": "rejected", "note": "Not needed",
    })
    assert r.status_code == 200


def test_update_governance_settings(client, campus_admin_headers):
    r = client.put("/api/governance/settings/me", headers=campus_admin_headers, json={
        "attendance_retention_days": 365,
        "audit_log_retention_days": 1000,
        "import_file_retention_days": 90,
        "auto_delete_enabled": False,
    })
    assert r.status_code == 200


def test_run_retention_dry_run(client, campus_admin_headers):
    r = client.post("/api/governance/run-retention", headers=campus_admin_headers, json={
        "dry_run": True,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["dry_run"] is True


def test_governance_requests_require_auth(client):
    r = client.get("/api/governance/requests")
    assert r.status_code == 401

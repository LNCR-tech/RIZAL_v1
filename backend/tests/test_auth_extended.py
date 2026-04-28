def test_change_password(client, student_headers):
    r = client.post("/auth/change-password", headers=student_headers, json={
        "current_password": "TestPass123!",
        "new_password": "TestPass123!",
    })
    assert r.status_code in (200, 400, 422)


def test_change_password_requires_auth(client):
    r = client.post("/auth/change-password", json={"current_password": "x", "new_password": "y"})
    assert r.status_code == 401


def test_forgot_password(client):
    r = client.post("/auth/forgot-password", json={"email": "student@test.com"})
    assert r.status_code in (200, 202, 404)


def test_password_reset_requests_requires_auth(client):
    r = client.get("/auth/password-reset-requests")
    assert r.status_code == 401


def test_password_reset_requests_admin(client, campus_admin_headers):
    r = client.get("/auth/password-reset-requests", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_password_change_prompt_dismiss(client, student_headers):
    r = client.post("/auth/password-change-prompt/dismiss", headers=student_headers)
    assert r.status_code in (200, 204)

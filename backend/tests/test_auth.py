def test_login_valid(client):
    r = client.post("/login", json={"email": "campus_admin@test.com", "password": "TestPass123!"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    r = client.post("/login", json={"email": "campus_admin@test.com", "password": "wrongpassword"})
    assert r.status_code == 401


def test_login_unknown_email(client):
    r = client.post("/login", json={"email": "nobody@test.com", "password": "TestPass123!"})
    assert r.status_code == 401


def test_token_endpoint(client):
    r = client.post("/token", data={"username": "campus_admin@test.com", "password": "TestPass123!"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_protected_endpoint_without_token(client):
    r = client.get("/api/users/me/")
    assert r.status_code == 401

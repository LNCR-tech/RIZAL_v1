def test_get_me_admin(client, admin_headers):
    r = client.get("/api/users/me/", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "admin@test.local"


def test_get_me_student(client, student_headers):
    r = client.get("/api/users/me/", headers=student_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "student@test.local"


def test_list_users_campus_admin(client, campus_admin_headers):
    r = client.get("/api/users/", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_users_student_forbidden(client, student_headers):
    r = client.get("/api/users/", headers=student_headers)
    assert r.status_code == 403


def test_create_user(client, campus_admin_headers):
    r = client.post("/api/users/", headers=campus_admin_headers, json={
        "email": "newuser@test.local",
        "first_name": "New",
        "last_name": "User",
        "roles": ["student"],
        "password": "NewPass123!"
    })
    assert r.status_code in (200, 201)
    assert r.json()["email"] == "newuser@test.local"


def test_update_own_profile(client, student_headers):
    me = client.get("/api/users/me/", headers=student_headers).json()
    r = client.patch(f"/api/users/{me['id']}", headers=student_headers, json={"first_name": "Updated"})
    assert r.status_code == 200
    assert r.json()["first_name"] == "Updated"

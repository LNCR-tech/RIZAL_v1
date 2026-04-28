def test_admin_list_schools(client, admin_headers):
    r = client.get("/api/school/admin/list", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_list_school_it_accounts(client, admin_headers):
    r = client.get("/api/school/admin/school-it-accounts", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_list_schools_requires_admin(client, campus_admin_headers):
    r = client.get("/api/school/admin/list", headers=campus_admin_headers)
    assert r.status_code == 403


def test_admin_list_schools_requires_auth(client):
    r = client.get("/api/school/admin/list")
    assert r.status_code == 401


def test_admin_create_school_with_school_it(client, admin_headers):
    import time
    unique = str(int(time.time()))
    r = client.post("/api/school/admin/create-school-it", data={
        "school_name": "New Test School",
        "primary_color": "#123456",
        "school_it_email": "newschoolit@test.com",
        "school_it_first_name": "New",
        "school_it_last_name": "SchoolIT",
        "school_it_password": "TestPass123!",
    })
    # Requires admin auth
    assert r.status_code == 401

    r = client.post("/api/school/admin/create-school-it", headers=admin_headers, data={
        "school_name": f"New Test School {unique}",
        "primary_color": "#123456",
        "school_it_email": f"newschoolit{unique}@test.com",
        "school_it_first_name": "New",
        "school_it_last_name": "SchoolIT",
        "school_it_password": "TestPass123!",
    })
    assert r.status_code == 200, r.text

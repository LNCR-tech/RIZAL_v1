import pytest


@pytest.fixture(scope="module")
def dept_id(client, campus_admin_headers):
    r = client.post("/api/departments/", headers=campus_admin_headers, json={"name": "Dept For Testing"})
    assert r.status_code == 201
    return r.json()["id"]


def test_list_departments(client, campus_admin_headers):
    r = client.get("/api/departments/", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_department(client, campus_admin_headers, dept_id):
    r = client.get(f"/api/departments/{dept_id}", headers=campus_admin_headers)
    assert r.status_code == 200
    assert r.json()["id"] == dept_id


def test_update_department(client, campus_admin_headers, dept_id):
    r = client.patch(f"/api/departments/{dept_id}", headers=campus_admin_headers, json={"name": "Dept Updated"})
    assert r.status_code == 200
    assert r.json()["name"] == "Dept Updated"


def test_delete_department(client, campus_admin_headers, dept_id):
    r = client.delete(f"/api/departments/{dept_id}", headers=campus_admin_headers)
    assert r.status_code == 204

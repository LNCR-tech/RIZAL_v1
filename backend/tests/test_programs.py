import pytest


@pytest.fixture(scope="module")
def prog_id(client, campus_admin_headers):
    r = client.post("/api/programs/", headers=campus_admin_headers, json={"name": "Program For Testing"})
    assert r.status_code == 201
    return r.json()["id"]


def test_list_programs(client, campus_admin_headers):
    r = client.get("/api/programs/", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_program(client, campus_admin_headers, prog_id):
    r = client.get(f"/api/programs/{prog_id}", headers=campus_admin_headers)
    assert r.status_code == 200
    assert r.json()["id"] == prog_id


def test_update_program(client, campus_admin_headers, prog_id):
    r = client.patch(f"/api/programs/{prog_id}", headers=campus_admin_headers, json={"name": "Program Updated"})
    assert r.status_code == 200
    assert r.json()["name"] == "Program Updated"


def test_delete_program(client, campus_admin_headers, prog_id):
    r = client.delete(f"/api/programs/{prog_id}", headers=campus_admin_headers)
    assert r.status_code == 204

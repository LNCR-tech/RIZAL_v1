import pytest


@pytest.fixture(scope="module")
def unit_id(client, campus_admin_headers):
    r = client.post("/api/governance/units/", headers=campus_admin_headers, json={
        "unit_code": "SSG-TEST",
        "unit_name": "Test SSG",
        "unit_type": "SSG",
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_list_governance_units(client, campus_admin_headers):
    r = client.get("/api/governance/units/", headers=campus_admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_governance_unit(client, campus_admin_headers, unit_id):
    r = client.get(f"/api/governance/units/{unit_id}", headers=campus_admin_headers)
    assert r.status_code == 200
    assert r.json()["id"] == unit_id


def test_update_governance_unit(client, campus_admin_headers, unit_id):
    r = client.patch(f"/api/governance/units/{unit_id}", headers=campus_admin_headers, json={
        "unit_name": "Updated SSG"
    })
    assert r.status_code == 200
    assert r.json()["unit_name"] == "Updated SSG"


def test_student_cannot_create_unit(client, student_headers):
    r = client.post("/api/governance/units/", headers=student_headers, json={
        "unit_code": "SSG-FAIL",
        "unit_name": "Fail SSG",
        "unit_type": "SSG",
    })
    assert r.status_code == 403

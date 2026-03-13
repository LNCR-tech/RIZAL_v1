from app.models import School, User, Role, UserRole
from app.core.security import create_access_token


def _create_school(test_db, *, code: str) -> School:
    school = School(
        name=f"Test School {code}",
        school_name=f"Test School {code}",
        school_code=code,
        address="Test Address",
    )
    test_db.add(school)
    test_db.commit()
    return school


def test_create_user_api_requires_auth(client):
    response = client.post(
        "/users/",
        json={
            "email": "apitest@example.com",
            "password": "StrongPassword123!",
            "first_name": "API",
            "middle_name": "",
            "last_name": "Test",
                "roles": ["student"]
        }
    )
    assert response.status_code == 401


def test_user_authentication(client, test_db):
    school = _create_school(test_db, code="AUTH-SCH")
    role = Role(name="student")
    test_db.add(role)
    test_db.commit()

    user = User(
        email="auth@example.com",
        school_id=school.id,
        first_name="Auth",
        last_name="Test",
        must_change_password=False,
    )
    user.set_password("AuthPassword123!")
    test_db.add(user)
    test_db.commit()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    test_db.add(user_role)
    test_db.commit()

    response = client.post(
        "/token",
        data={
            "username": "auth@example.com",
            "password": "AuthPassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    response = client.post(
        "/token",
        data={
            "username": "auth@example.com",
            "password": "WrongPassword",
        },
    )
    assert response.status_code == 401


def test_protected_endpoint(client, test_db):
    role = Role(name="student")
    test_db.add(role)
    test_db.commit()

    user = User(
        email="student@example.com",
        first_name="Student",
        last_name="Test",
        must_change_password=False,
    )
    user.set_password("StudentPass123!")
    test_db.add(user)
    test_db.commit()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    test_db.add(user_role)
    test_db.commit()

    token = create_access_token({"sub": user.email})

    response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "student@example.com"

    response = client.get("/users/me/")
    assert response.status_code == 401

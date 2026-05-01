import pytest
from app.models.user import User, UserRole
from app.models.role import Role
from app.models.school import School
from app.core.database import SessionLocal
from app.utils.passwords import hash_password_bcrypt

# Matrix of routes and expected status codes for each role
# (route, method, role, expected_status)
RBAC_MATRIX = [
    # Public routes
    ("/health", "GET", "unauthenticated", 200),
    ("/api/v1/auth/login", "POST", "unauthenticated", 422), # 422 because missing payload, but route is accessible
    
    # Admin routes — actual path is /api/school/admin/list
    ("/api/school/admin/list", "GET", "admin", 200),
    ("/api/school/admin/list", "GET", "campus_admin", 403),
    ("/api/school/admin/list", "GET", "student", 403),
    ("/api/school/admin/list", "GET", "unauthenticated", 401),
    
    # Campus Admin routes
    ("/api/v1/users/", "GET", "admin", 200),
    ("/api/v1/users/", "GET", "campus_admin", 200),
    ("/api/v1/users/", "GET", "ssg", 403),
    ("/api/v1/users/", "GET", "student", 403),
    
    # Event creation
    ("/api/v1/events/", "POST", "admin", 200), # Might be 422 due to missing payload, but 403 blocks first
    ("/api/v1/events/", "POST", "campus_admin", 422), # Allowed, but bad payload
    ("/api/v1/events/", "POST", "student", 403),
    
    # Student own profile
    ("/api/v1/users/me", "GET", "student", 200),
    ("/api/v1/users/me", "GET", "unauthenticated", 401),
]

@pytest.fixture(scope="session")
def ssg_token(client):
    db = SessionLocal()
    try:
        school = db.query(School).filter_by(school_code="TEST-001").first()
        ssg_user = db.query(User).filter_by(email="ssg@test.com").first()
        if not ssg_user:
            role = db.query(Role).filter_by(code="ssg").first()
            school_id = school.id if school else None
            ssg_user = User(email="ssg@test.com", first_name="Test", last_name="SSG", school_id=school_id, password_hash=hash_password_bcrypt("TestPass123!"))
            db.add(ssg_user)
            db.flush()
            db.add(UserRole(user_id=ssg_user.id, role_id=role.id))
            db.commit()
    finally:
        db.close()
        
    r = client.post("/api/v1/auth/login", json={"email": "ssg@test.com", "password": "TestPass123!"})
    if r.status_code == 404:
         # fallback to /login if /api/v1/auth/login is not the path
         r = client.post("/login", json={"email": "ssg@test.com", "password": "TestPass123!"})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.mark.parametrize("route, method, role, expected_status", RBAC_MATRIX)
def test_rbac_matrix(client, route, method, role, expected_status, admin_token, campus_admin_token, student_token, ssg_token):
    headers = {}
    if role == "admin":
        headers["Authorization"] = f"Bearer {admin_token}"
    elif role == "campus_admin":
        headers["Authorization"] = f"Bearer {campus_admin_token}"
    elif role == "student":
        headers["Authorization"] = f"Bearer {student_token}"
    elif role == "ssg":
        headers["Authorization"] = f"Bearer {ssg_token}"
        
    if method == "GET":
        r = client.get(route, headers=headers)
    elif method == "POST":
        r = client.post(route, headers=headers, json={})
        
    # We accept 422 as "allowed but bad payload" to differentiate from 403 "forbidden"
    if expected_status == 200 and r.status_code == 422:
        assert True
    else:
        assert r.status_code == expected_status, f"Expected {expected_status} for {role} on {method} {route}, got {r.status_code}"

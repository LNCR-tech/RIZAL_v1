import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:cmpjdatabase@127.0.0.1:5432/fastapi_db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("RATE_LIMIT_FAIL_OPEN", "true")
os.environ.setdefault("FACE_SCAN_BYPASS_ALL", "true")
os.environ.setdefault("PRIVILEGED_FACE_VERIFICATION_ENABLED", "false")
os.environ.setdefault("EMAIL_TRANSPORT", "disabled")
os.environ.setdefault("API_DOCS_ENABLED", "true")

from app.main import app
from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.user import User, UserRole, StudentProfile
from app.models.school import School, SchoolBranding, SchoolEventPolicy
from app.models.role import Role
from app.models.department import Department
from app.models.program import Program
from app.models.attendance import AttendanceMethodLookup, AttendanceStatusLookup
from app.utils.passwords import hash_password_bcrypt


# ---------------------------------------------------------------------------
# DB session — each test runs in a transaction that is rolled back after
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    _seed(session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def _seed(db: Session):
    # Lookup tables
    for code, name in [("present", "Present"), ("late", "Late"), ("absent", "Absent"), ("excused", "Excused")]:
        if not db.query(AttendanceStatusLookup).filter_by(code=code).first():
            db.add(AttendanceStatusLookup(code=code, display_name=name))
    for code, name in [("manual", "Manual"), ("face_scan", "Face Scan"), ("rfid", "RFID"), ("qr", "QR")]:
        if not db.query(AttendanceMethodLookup).filter_by(code=code).first():
            db.add(AttendanceMethodLookup(code=code, display_name=name))

    # Roles
    roles = {}
    for code, display in [("admin", "Admin"), ("campus_admin", "Campus Admin"), ("student", "Student"), ("ssg", "SSG"), ("teacher", "Teacher")]:
        role = db.query(Role).filter_by(code=code).first()
        if not role:
            role = Role(code=code, display_name=display)
            db.add(role)
            db.flush()
        roles[code] = role

    # School
    school = db.query(School).filter_by(school_code="TEST-001").first()
    if not school:
        school = School(school_code="TEST-001", legal_name="Test School", display_name="Test School", address="123 Test St", is_active=True)
        db.add(school)
        db.flush()
        db.add(SchoolBranding(school_id=school.id, primary_color="#162F65"))
        db.add(SchoolEventPolicy(school_id=school.id, default_early_check_in_minutes=30, default_late_threshold_minutes=10, default_sign_out_grace_minutes=20))

    # Department + Program
    dept = db.query(Department).filter_by(school_id=school.id, name="Test Department").first()
    if not dept:
        dept = Department(school_id=school.id, name="Test Department")
        db.add(dept)
        db.flush()

    prog = db.query(Program).filter_by(school_id=school.id, name="Test Program").first()
    if not prog:
        prog = Program(school_id=school.id, name="Test Program")
        db.add(prog)
        db.flush()

    # Users
    def _make_user(email, role_code, school_id=None):
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(email=email, school_id=school_id, first_name="Test", last_name=role_code.title(),
                        password_hash=hash_password_bcrypt("TestPass123!"), must_change_password=False)
            db.add(user)
            db.flush()
            db.add(UserRole(user_id=user.id, role_id=roles[role_code].id))
            db.flush()
        return user

    _make_user("admin@test.local", "admin", school_id=None)
    campus_admin = _make_user("campus_admin@test.local", "campus_admin", school_id=school.id)
    student_user = _make_user("student@test.local", "student", school_id=school.id)

    # Student profile
    if not db.query(StudentProfile).filter_by(user_id=student_user.id).first():
        db.add(StudentProfile(user_id=student_user.id, school_id=school.id, student_number="STU-001",
                              department_id=dept.id, program_id=prog.id, year_level=1))

    db.flush()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client(db_session):
    from app.core.dependencies import get_db

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth tokens via /login
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post("/login", json={"email": "admin@test.local", "password": "TestPass123!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def campus_admin_token(client):
    r = client.post("/login", json={"email": "campus_admin@test.local", "password": "TestPass123!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def student_token(client):
    r = client.post("/login", json={"email": "student@test.local", "password": "TestPass123!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def campus_admin_headers(campus_admin_token):
    return {"Authorization": f"Bearer {campus_admin_token}"}


@pytest.fixture(scope="session")
def student_headers(student_token):
    return {"Authorization": f"Bearer {student_token}"}

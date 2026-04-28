from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.security import authenticate_user, verify_user_password
from app.models import Base
from app.models.associations import program_department_association
from app.models.department import Department
from app.models.platform_features import NotificationLog, UserNotificationPreference
from app.models.program import Program
from app.models.role import Role
from app.models.school import School
from app.models.password_reset_request import PasswordResetRequest
from app.models.user import StudentProfile, User, UserRole
from app.routers import auth
from app.routers.auth import request_forgot_password
from app.routers.users.students import create_student_account
from app.schemas.auth import ChangePasswordRequest
from app.schemas.password_reset import ForgotPasswordRequestCreate
from app.schemas.user import StudentAccountCreate
from app.services.notification_center_service import send_notification_to_user
from app.services.student_import_service import StudentImportService
from app.utils.passwords import hash_password_bcrypt, verify_password_bcrypt


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=engine,
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _seed_school_scope(db):
    school = School(
        name="Test School",
        school_name="Test School",
        address="Test Address",
        primary_color="#162F65",
    )
    db.add(school)
    db.flush()

    department = Department(school_id=school.id, name="Engineering")
    program = Program(school_id=school.id, name="BSIT")
    student_role = Role(name="student")
    campus_admin_role = Role(name="campus_admin")
    db.add_all([department, program, student_role, campus_admin_role])
    db.flush()
    db.execute(
        program_department_association.insert().values(
            program_id=program.id,
            department_id=department.id,
        )
    )

    admin = User(
        email="campus@example.edu",
        school_id=school.id,
        first_name="Campus",
        last_name="Admin",
        is_active=True,
        must_change_password=False,
        should_prompt_password_change=False,
    )
    admin.set_password("AdminPass1")
    db.add(admin)
    db.flush()
    db.add(UserRole(user_id=admin.id, role_id=campus_admin_role.id))
    db.commit()

    return SimpleNamespace(
        school=school,
        department=department,
        program=program,
        student_role=student_role,
        campus_admin_role=campus_admin_role,
        admin=admin,
    )


def _create_student(
    db,
    *,
    email: str = "student@example.edu",
    first_name: str = "Student",
    last_name: str = "Santos",
    password_hash: str | None = None,
    using_default_import_password: bool = True,
):
    scope = _seed_school_scope(db)
    user = User(
        email=email,
        school_id=scope.school.id,
        first_name=first_name,
        last_name=last_name,
        password_hash=password_hash or hash_password_bcrypt(last_name.lower()),
        is_active=True,
        must_change_password=False,
        should_prompt_password_change=False,
        using_default_import_password=using_default_import_password,
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=scope.student_role.id))
    db.add(
        StudentProfile(
            user_id=user.id,
            school_id=scope.school.id,
            student_id="STU-001",
            department_id=scope.department.id,
            program_id=scope.program.id,
            year_level=1,
        )
    )
    db.commit()
    return scope, user


def _request():
    return SimpleNamespace(headers={}, client=SimpleNamespace(host="127.0.0.1"))


def test_bulk_import_default_password_is_lowercase_last_name_and_case_insensitive_login():
    row = {"last_name": "De Luna"}

    StudentImportService()._attach_import_password_credentials(row)

    assert row["temporary_password"] == "de luna"
    assert verify_password_bcrypt("de luna", row["password_hash"])

    user = User(
        email="student@example.edu",
        first_name="Dee",
        last_name="De Luna",
        password_hash=row["password_hash"],
        using_default_import_password=True,
    )
    assert verify_user_password(user, "DE LUNA")


def test_manual_student_creation_uses_same_default_password(db_session):
    scope = _seed_school_scope(db_session)

    create_student_account(
        StudentAccountCreate(
            email="manual@example.edu",
            first_name="Manual",
            middle_name=None,
            last_name="LaGas",
            student_id="MAN-001",
            department_id=scope.department.id,
            program_id=scope.program.id,
            year_level=1,
        ),
        current_user=scope.admin,
        db=db_session,
    )

    created = db_session.query(User).filter(User.email == "manual@example.edu").one()
    assert created.using_default_import_password is True
    assert verify_password_bcrypt("lagas", created.password_hash)
    assert authenticate_user(db_session, "manual@example.edu", "LAGAS") == created


def test_change_password_accepts_mixed_case_default_then_becomes_case_sensitive(db_session):
    _, user = _create_student(db_session, last_name="Santos")

    auth.change_password(
        ChangePasswordRequest(current_password="SANTOS", new_password="NewPass1"),
        current_user=user,
        db=db_session,
    )
    db_session.refresh(user)

    assert user.using_default_import_password is False
    assert authenticate_user(db_session, user.email, "NewPass1") == user
    assert authenticate_user(db_session, user.email, "NEWPASS1") is None


def test_forgot_password_auto_resets_students_only_and_clears_pending_requests(db_session, monkeypatch):
    scope, student = _create_student(
        db_session,
        email="forgot.student@example.edu",
        last_name="ReYes",
        password_hash=hash_password_bcrypt("ChangedPass1"),
        using_default_import_password=False,
    )
    non_student = User(
        email="campus.reset@example.edu",
        school_id=scope.school.id,
        first_name="Campus",
        last_name="Reset",
        password_hash=hash_password_bcrypt("OldPass1"),
        is_active=True,
        must_change_password=False,
        should_prompt_password_change=False,
        using_default_import_password=False,
    )
    db_session.add(non_student)
    db_session.flush()
    db_session.add(UserRole(user_id=non_student.id, role_id=scope.campus_admin_role.id))
    pending = PasswordResetRequest(
        user_id=student.id,
        school_id=scope.school.id,
        requested_email=student.email,
        status="pending",
    )
    db_session.add(pending)
    db_session.commit()

    monkeypatch.setattr(auth, "enforce_rate_limit", lambda *args, **kwargs: None)

    request_forgot_password(
        _request(),
        ForgotPasswordRequestCreate(email="FORGOT.STUDENT@example.edu"),
        db_session,
    )
    request_forgot_password(
        _request(),
        ForgotPasswordRequestCreate(email=non_student.email),
        db_session,
    )
    db_session.refresh(student)
    db_session.refresh(non_student)
    db_session.refresh(pending)

    assert student.using_default_import_password is True
    assert student.must_change_password is False
    assert student.should_prompt_password_change is True
    assert authenticate_user(db_session, student.email, "REYES") == student
    assert pending.status == "auto_reset"
    assert pending.resolved_at is not None

    assert non_student.using_default_import_password is False
    assert verify_password_bcrypt("OldPass1", non_student.password_hash)
    assert authenticate_user(db_session, non_student.email, "reset") is None


def test_notifications_skip_email_channel_when_code_disabled(db_session):
    _, student = _create_student(db_session, email="notify.student@example.edu")
    db_session.add(
        UserNotificationPreference(
            user_id=student.id,
            email_enabled=True,
            sms_enabled=False,
            notify_account_security=True,
        )
    )
    db_session.commit()

    status = send_notification_to_user(
        db_session,
        user=student,
        school_id=student.school_id,
        category="account_security",
        subject="Password Changed",
        message="Your password was changed.",
        deliver_in_app=True,
    )
    db_session.commit()

    logs = db_session.execute(
        select(NotificationLog).where(NotificationLog.user_id == student.id)
    ).scalars().all()

    assert status == "sent"
    assert {(log.channel, log.status) for log in logs} == {
        ("in_app", "sent"),
        ("email", "skipped"),
    }

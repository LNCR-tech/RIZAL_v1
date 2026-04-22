from datetime import datetime

from app.core.security import create_access_token
from app.models import Department, Program, Role, School, StudentProfile, User, UserRole
from app.models.platform_features import LoginHistory


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token({"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


def _create_school(test_db, *, code: str) -> School:
    school = School(
        name=f"School {code}",
        school_name=f"School {code}",
        school_code=code,
        address="Test Address",
    )
    test_db.add(school)
    test_db.commit()
    return school


def _create_role(test_db, *, name: str) -> Role:
    role = Role(name=name)
    test_db.add(role)
    test_db.commit()
    return role


def _create_user(
    test_db,
    *,
    email: str,
    school_id: int,
    role_ids: list[int] | None = None,
) -> User:
    user = User(
        email=email,
        school_id=school_id,
        first_name="Test",
        last_name="User",
        must_change_password=False,
    )
    user.set_password("Password123!")
    test_db.add(user)
    test_db.commit()

    for role_id in role_ids or []:
        test_db.add(UserRole(user_id=user.id, role_id=role_id))
    test_db.commit()
    return user


def _create_scope(test_db, *, school_id: int, department_name: str, program_name: str) -> tuple[Department, Program]:
    department = Department(name=department_name, school_id=school_id)
    program = Program(name=program_name, school_id=school_id)
    program.departments.append(department)
    test_db.add_all([department, program])
    test_db.commit()
    return department, program


def _create_student_profile(
    test_db,
    *,
    user_id: int,
    school_id: int,
    student_id: str,
    department_id: int,
    program_id: int,
) -> StudentProfile:
    profile = StudentProfile(
        user_id=user_id,
        school_id=school_id,
        student_id=student_id,
        department_id=department_id,
        program_id=program_id,
        year_level=1,
    )
    test_db.add(profile)
    test_db.commit()
    return profile


def test_school_summary_includes_student_login_report(client, test_db):
    school = _create_school(test_db, code="LOGIN-REPORT")
    other_school = _create_school(test_db, code="OTHER")
    campus_admin_role = _create_role(test_db, name="campus_admin")
    student_role = _create_role(test_db, name="student")
    department, program = _create_scope(
        test_db,
        school_id=school.id,
        department_name="Engineering",
        program_name="Computer Science",
    )
    other_department, other_program = _create_scope(
        test_db,
        school_id=other_school.id,
        department_name="Business",
        program_name="Accounting",
    )

    campus_admin = _create_user(
        test_db,
        email="campus.admin@example.com",
        school_id=school.id,
        role_ids=[campus_admin_role.id],
    )
    logged_in_user = _create_user(
        test_db,
        email="logged.in.student@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )
    stale_login_user = _create_user(
        test_db,
        email="stale.login.student@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )
    other_school_user = _create_user(
        test_db,
        email="other.school.student@example.com",
        school_id=other_school.id,
        role_ids=[student_role.id],
    )

    _create_student_profile(
        test_db,
        user_id=logged_in_user.id,
        school_id=school.id,
        student_id="STU-001",
        department_id=department.id,
        program_id=program.id,
    )
    _create_student_profile(
        test_db,
        user_id=stale_login_user.id,
        school_id=school.id,
        student_id="STU-002",
        department_id=department.id,
        program_id=program.id,
    )
    _create_student_profile(
        test_db,
        user_id=other_school_user.id,
        school_id=other_school.id,
        student_id="STU-003",
        department_id=other_department.id,
        program_id=other_program.id,
    )

    test_db.add_all([
        LoginHistory(
            user_id=logged_in_user.id,
            school_id=school.id,
            email_attempted=logged_in_user.email,
            success=True,
            auth_method="password",
            created_at=datetime(2026, 4, 10, 8, 30, 0),
        ),
        LoginHistory(
            user_id=logged_in_user.id,
            school_id=school.id,
            email_attempted=logged_in_user.email,
            success=True,
            auth_method="password",
            created_at=datetime(2026, 4, 12, 9, 45, 0),
        ),
        LoginHistory(
            user_id=stale_login_user.id,
            school_id=school.id,
            email_attempted=stale_login_user.email,
            success=True,
            auth_method="password",
            created_at=datetime(2026, 3, 25, 10, 0, 0),
        ),
        LoginHistory(
            user_id=stale_login_user.id,
            school_id=school.id,
            email_attempted=stale_login_user.email,
            success=False,
            auth_method="password",
            failure_reason="invalid_credentials",
            created_at=datetime(2026, 4, 14, 8, 0, 0),
        ),
        LoginHistory(
            user_id=other_school_user.id,
            school_id=other_school.id,
            email_attempted=other_school_user.email,
            success=True,
            auth_method="password",
            created_at=datetime(2026, 4, 9, 11, 0, 0),
        ),
    ])
    test_db.commit()

    response = client.get(
        "/api/attendance/summary",
        params={
            "start_date": "2026-04-01",
            "end_date": "2026-04-30",
        },
        headers=_auth_headers(campus_admin),
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["student_login_summary"] == {
        "total_students": 2,
        "logged_in_students": 1,
        "not_logged_in_students": 1,
        "login_coverage_rate": 50.0,
    }

    rows_by_student_id = {
        row["student_id"]: row
        for row in payload["student_login_rows"]
    }
    assert set(rows_by_student_id) == {"STU-001", "STU-002"}

    assert rows_by_student_id["STU-001"]["has_logged_in"] is True
    assert rows_by_student_id["STU-001"]["successful_login_count"] == 2
    assert rows_by_student_id["STU-001"]["last_login_at"].startswith("2026-04-12T09:45:00")

    assert rows_by_student_id["STU-002"]["has_logged_in"] is False
    assert rows_by_student_id["STU-002"]["successful_login_count"] == 0
    assert rows_by_student_id["STU-002"]["last_login_at"] is None

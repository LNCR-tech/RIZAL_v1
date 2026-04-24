from datetime import datetime

from app.core.security import create_access_token
from app.models import Role, School, SchoolAuditLog, User, UserRole


def _create_school(test_db, *, code: str) -> School:
    school = School(
        name=f"Audit School {code}",
        school_name=f"Audit School {code}",
        school_code=code,
        address="Audit Address",
    )
    test_db.add(school)
    test_db.commit()
    return school


def _create_user_with_role(
    test_db,
    *,
    email: str,
    role_name: str,
    password: str,
    school_id: int | None = None,
) -> User:
    role = test_db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name)
        test_db.add(role)
        test_db.commit()

    user = User(
        email=email,
        school_id=school_id,
        first_name="Audit",
        last_name="User",
        must_change_password=False,
    )
    user.set_password(password)
    test_db.add(user)
    test_db.commit()

    test_db.add(UserRole(user_id=user.id, role_id=role.id))
    test_db.commit()
    return user


def _auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': user.email})}"}


def test_system_audit_logs_return_philippine_time(client, test_db):
    school = _create_school(test_db, code="AUDIT-TZ-SYS")
    campus_admin = _create_user_with_role(
        test_db,
        email="campus.audit@example.com",
        role_name="campus_admin",
        password="CampusPass123!",
        school_id=school.id,
    )
    audit_log = SchoolAuditLog(
        school_id=school.id,
        actor_user_id=campus_admin.id,
        action="branding_update",
        status="success",
        details="{}",
        created_at=datetime(2026, 4, 22, 0, 30, 0),
    )
    test_db.add(audit_log)
    test_db.commit()

    response = client.get(
        "/api/audit-logs",
        headers=_auth_headers(campus_admin),
    )

    assert response.status_code == 200
    created_at = response.json()["items"][0]["created_at"]
    assert created_at == "2026-04-22T08:30:00+08:00"


def test_school_settings_audit_logs_return_philippine_time(client, test_db):
    school = _create_school(test_db, code="AUDIT-TZ-SCHOOL")
    campus_admin = _create_user_with_role(
        test_db,
        email="campus.settings.audit@example.com",
        role_name="campus_admin",
        password="CampusPass123!",
        school_id=school.id,
    )
    audit_log = SchoolAuditLog(
        school_id=school.id,
        actor_user_id=campus_admin.id,
        action="school_update",
        status="success",
        details="{}",
        created_at=datetime(2026, 4, 22, 1, 15, 0),
    )
    test_db.add(audit_log)
    test_db.commit()

    response = client.get(
        "/school-settings/me/audit-logs",
        headers=_auth_headers(campus_admin),
    )

    assert response.status_code == 200
    created_at = response.json()[0]["created_at"]
    assert created_at == "2026-04-22T09:15:00+08:00"

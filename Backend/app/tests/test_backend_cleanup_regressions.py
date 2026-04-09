from datetime import date, timedelta

from app.core.security import create_access_token
from app.models import DataRequest, Role, School, SchoolSubscriptionReminder, User, UserRole


def _create_school(test_db, *, code: str, renewal_date: date | None = None) -> School:
    school = School(
        name=f"Test School {code}",
        school_name=f"Test School {code}",
        school_code=code,
        address="Test Address",
        subscription_end=renewal_date,
    )
    test_db.add(school)
    test_db.commit()
    return school


def _get_or_create_role(test_db, *, name: str) -> Role:
    role = test_db.query(Role).filter(Role.name == name).first()
    if role is None:
        role = Role(name=name)
        test_db.add(role)
        test_db.commit()
    return role


def _create_user_with_role(
    test_db,
    *,
    email: str,
    role_name: str,
    password: str,
    school_id: int | None = None,
) -> User:
    role = _get_or_create_role(test_db, name=role_name)
    user = User(
        email=email,
        school_id=school_id,
        first_name="Test",
        last_name="User",
        must_change_password=False,
        is_active=True,
    )
    user.set_password(password)
    test_db.add(user)
    test_db.commit()

    test_db.add(UserRole(user_id=user.id, role_id=role.id))
    test_db.commit()
    return user


def _auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': user.email})}"}


def test_governance_request_rejects_cross_school_target_for_regular_user(client, test_db):
    school_one = _create_school(test_db, code="GOV-REQ-1")
    school_two = _create_school(test_db, code="GOV-REQ-2")
    requester = _create_user_with_role(
        test_db,
        email="requester@example.com",
        role_name="student",
        password="StudentPass123!",
        school_id=school_one.id,
    )
    target = _create_user_with_role(
        test_db,
        email="target@example.com",
        role_name="student",
        password="StudentPass123!",
        school_id=school_two.id,
    )

    response = client.post(
        "/api/governance/requests",
        headers=_auth_headers(requester),
        json={
            "request_type": "export",
            "target_user_id": target.id,
            "reason": "Attempt cross-school export",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Users can only create data requests for their own account."
    assert test_db.query(DataRequest).count() == 0


def test_governance_settings_reject_unknown_school_for_platform_admin(client, test_db):
    platform_admin = _create_user_with_role(
        test_db,
        email="platform.admin@example.com",
        role_name="admin",
        password="AdminPass123!",
    )

    response = client.get(
        "/api/governance/settings/me?school_id=999999",
        headers=_auth_headers(platform_admin),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"


def test_subscription_run_reminders_initializes_missing_settings_for_platform_admin(
    client, test_db, monkeypatch
):
    school = _create_school(
        test_db,
        code="SUB-REMIND",
        renewal_date=date.today() + timedelta(days=1),
    )
    platform_admin = _create_user_with_role(
        test_db,
        email="platform.sub.admin@example.com",
        role_name="admin",
        password="AdminPass123!",
    )
    campus_admin = _create_user_with_role(
        test_db,
        email="campus.sub.admin@example.com",
        role_name="campus_admin",
        password="CampusPass123!",
        school_id=school.id,
    )

    def _fake_send_notification_to_user(*args, **kwargs):
        return "sent"

    monkeypatch.setattr(
        "app.routers.subscription.send_notification_to_user",
        _fake_send_notification_to_user,
    )

    response = client.post(
        "/api/subscription/run-reminders",
        headers=_auth_headers(platform_admin),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schools_checked"] >= 1
    assert payload["reminders_created"] == 1
    assert payload["reminders_sent"] == 1

    reminder = (
        test_db.query(SchoolSubscriptionReminder)
        .filter(SchoolSubscriptionReminder.school_id == school.id)
        .first()
    )
    assert reminder is not None
    assert reminder.status == "sent"


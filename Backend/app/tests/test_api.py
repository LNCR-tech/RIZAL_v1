from datetime import datetime, timedelta

from app.models import Event, School, SchoolSetting, User, Role, UserRole
from app.core.security import create_access_token, verify_password
from app.utils.passwords import hash_password_bcrypt


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


def test_create_event_api_uses_default_attendance_window_values(client, test_db):
    school = _create_school(test_db, code="EVENT-DEFAULTS")
    admin_role = Role(name="admin")
    test_db.add(admin_role)
    test_db.commit()

    admin_user = User(
        email="event.defaults@example.com",
        school_id=school.id,
        first_name="Event",
        last_name="Defaults",
        must_change_password=False,
    )
    admin_user.set_password("AdminPass123!")
    test_db.add(admin_user)
    test_db.commit()

    test_db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
    test_db.commit()

    token = create_access_token({"sub": admin_user.email})
    start = datetime.utcnow().replace(microsecond=0) + timedelta(days=1)
    end = start + timedelta(hours=2)

    response = client.post(
        "/events/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Default Window Event",
            "location": "Main Gym",
            "start_datetime": start.isoformat(),
            "end_datetime": end.isoformat(),
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["early_check_in_minutes"] == 30
    assert payload["late_threshold_minutes"] == 10
    assert payload["sign_out_grace_minutes"] == 20

    created_event = test_db.query(Event).filter(Event.id == payload["id"]).first()
    assert created_event is not None
    assert created_event.early_check_in_minutes == 30
    assert created_event.late_threshold_minutes == 10
    assert created_event.sign_out_grace_minutes == 20


def test_school_event_defaults_are_used_for_new_events(client, test_db):
    school = _create_school(test_db, code="EVENT-SCHOOL-DEFAULTS")
    campus_admin_role = Role(name="campus_admin")
    test_db.add(campus_admin_role)
    test_db.commit()

    campus_admin = User(
        email="event.school.defaults@example.com",
        school_id=school.id,
        first_name="Campus",
        last_name="Admin",
        must_change_password=False,
    )
    campus_admin.set_password("CampusPass123!")
    test_db.add(campus_admin)
    test_db.commit()

    test_db.add(UserRole(user_id=campus_admin.id, role_id=campus_admin_role.id))
    test_db.commit()

    token = create_access_token({"sub": campus_admin.email})

    update_response = client.put(
        "/api/school/update",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "event_default_early_check_in_minutes": "45",
            "event_default_late_threshold_minutes": "12",
            "event_default_sign_out_grace_minutes": "25",
        },
    )

    assert update_response.status_code == 200
    update_payload = update_response.json()
    assert update_payload["event_default_early_check_in_minutes"] == 45
    assert update_payload["event_default_late_threshold_minutes"] == 12
    assert update_payload["event_default_sign_out_grace_minutes"] == 25

    start = datetime.utcnow().replace(microsecond=0) + timedelta(days=1)
    end = start + timedelta(hours=2)
    create_response = client.post(
        "/events/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "School Default Event",
            "location": "Auditorium",
            "start_datetime": start.isoformat(),
            "end_datetime": end.isoformat(),
        },
    )

    assert create_response.status_code == 201
    create_payload = create_response.json()
    assert create_payload["early_check_in_minutes"] == 45
    assert create_payload["late_threshold_minutes"] == 12
    assert create_payload["sign_out_grace_minutes"] == 25

    school_settings = test_db.query(SchoolSetting).filter(SchoolSetting.school_id == school.id).first()
    assert school_settings is not None
    assert school_settings.event_default_early_check_in_minutes == 45
    assert school_settings.event_default_late_threshold_minutes == 12
    assert school_settings.event_default_sign_out_grace_minutes == 25


def test_create_user_api_does_not_force_password_change_for_new_accounts(client, test_db):
    school = _create_school(test_db, code="USER-SCH")
    admin_role = Role(name="admin")
    student_role = Role(name="student")
    test_db.add_all([admin_role, student_role])
    test_db.commit()

    admin_user = User(
        email="schooladmin@example.com",
        school_id=school.id,
        first_name="School",
        last_name="Admin",
        must_change_password=False,
    )
    admin_user.set_password("AdminPass123!")
    test_db.add(admin_user)
    test_db.commit()

    test_db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
    test_db.commit()

    token = create_access_token({"sub": admin_user.email})

    response = client.post(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "fresh.user@example.com",
            "first_name": "Fresh",
            "middle_name": "",
            "last_name": "User",
            "roles": ["student"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["generated_temporary_password"]

    created_user = test_db.query(User).filter(User.email == "fresh.user@example.com").first()
    assert created_user is not None
    assert created_user.must_change_password is False
    assert created_user.should_prompt_password_change is True
    assert verify_password(payload["generated_temporary_password"], created_user.password_hash)


def test_change_password_accepts_current_password_for_model_hashed_user(client, test_db):
    school = _create_school(test_db, code="CHG-MODEL")
    role = Role(name="student")
    test_db.add(role)
    test_db.commit()

    user = User(
        email="change.model@example.com",
        school_id=school.id,
        first_name="Change",
        last_name="Model",
        must_change_password=True,
    )
    temporary_password = "TempPass123!"
    new_password = "NewPass123!"
    user.set_password(temporary_password)
    test_db.add(user)
    test_db.commit()

    test_db.add(UserRole(user_id=user.id, role_id=role.id))
    test_db.commit()

    token = create_access_token({"sub": user.email})

    response = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": temporary_password,
            "new_password": new_password,
        },
    )

    assert response.status_code == 200

    test_db.expire_all()
    updated_user = test_db.query(User).filter(User.id == user.id).first()
    assert updated_user is not None
    assert updated_user.must_change_password is False
    assert verify_password(new_password, updated_user.password_hash)


def test_change_password_accepts_current_password_for_passlib_hashed_user(client, test_db):
    school = _create_school(test_db, code="CHG-PASSLIB")
    role = Role(name="student")
    test_db.add(role)
    test_db.commit()

    temporary_password = "TempPass123!"
    new_password = "NewPass123!"
    user = User(
        email="change.passlib@example.com",
        school_id=school.id,
        first_name="Change",
        last_name="Passlib",
        must_change_password=True,
        password_hash=hash_password_bcrypt(temporary_password),
    )
    test_db.add(user)
    test_db.commit()

    test_db.add(UserRole(user_id=user.id, role_id=role.id))
    test_db.commit()

    token = create_access_token({"sub": user.email})

    response = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": temporary_password,
            "new_password": new_password,
        },
    )

    assert response.status_code == 200

    test_db.expire_all()
    updated_user = test_db.query(User).filter(User.id == user.id).first()
    assert updated_user is not None
    assert updated_user.must_change_password is False
    assert verify_password(new_password, updated_user.password_hash)


def test_login_response_recommends_password_change_when_prompt_flag_is_set(client, test_db):
    school = _create_school(test_db, code="PROMPT-SCH")
    role = Role(name="student")
    test_db.add(role)
    test_db.commit()

    user = User(
        email="prompted@example.com",
        school_id=school.id,
        first_name="Prompted",
        last_name="User",
        must_change_password=False,
        should_prompt_password_change=True,
    )
    user.set_password("PromptPass123!")
    test_db.add(user)
    test_db.commit()

    test_db.add(UserRole(user_id=user.id, role_id=role.id))
    test_db.commit()

    response = client.post(
        "/token",
        data={
            "username": "prompted@example.com",
            "password": "PromptPass123!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["must_change_password"] is False
    assert data["password_change_recommended"] is True


def test_change_password_clears_password_change_prompt_flag(client, test_db):
    school = _create_school(test_db, code="PROMPT-CLR")
    role = Role(name="student")
    test_db.add(role)
    test_db.commit()

    user = User(
        email="prompt.clear@example.com",
        school_id=school.id,
        first_name="Prompt",
        last_name="Clear",
        must_change_password=False,
        should_prompt_password_change=True,
    )
    user.set_password("PromptPass123!")
    test_db.add(user)
    test_db.commit()

    test_db.add(UserRole(user_id=user.id, role_id=role.id))
    test_db.commit()

    token = create_access_token({"sub": user.email})

    response = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "PromptPass123!",
            "new_password": "PromptPass456!",
        },
    )

    assert response.status_code == 200

    test_db.expire_all()
    updated_user = test_db.query(User).filter(User.id == user.id).first()
    assert updated_user is not None
    assert updated_user.should_prompt_password_change is False
    assert updated_user.must_change_password is False


def test_face_pending_user_can_change_password_during_onboarding(client, test_db):
    school = _create_school(test_db, code="FACE-CHG")
    role = Role(name="school_IT")
    test_db.add(role)
    test_db.commit()

    user = User(
        email="schoolit@example.com",
        school_id=school.id,
        first_name="School",
        last_name="IT",
        must_change_password=True,
    )
    user.set_password("TempPass123!")
    test_db.add(user)
    test_db.commit()

    test_db.add(UserRole(user_id=user.id, role_id=role.id))
    test_db.commit()

    token = create_access_token({"sub": user.email, "face_pending": True})

    response = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "TempPass123!",
            "new_password": "NextPass123!",
        },
    )

    assert response.status_code == 200


def test_face_pending_user_can_dismiss_password_change_prompt(client, test_db):
    school = _create_school(test_db, code="FACE-SKIP")
    role = Role(name="school_IT")
    test_db.add(role)
    test_db.commit()

    user = User(
        email="skip.prompt@example.com",
        school_id=school.id,
        first_name="Skip",
        last_name="Prompt",
        must_change_password=False,
        should_prompt_password_change=True,
    )
    user.set_password("SkipPass123!")
    test_db.add(user)
    test_db.commit()

    test_db.add(UserRole(user_id=user.id, role_id=role.id))
    test_db.commit()

    token = create_access_token({"sub": user.email, "face_pending": True})

    response = client.post(
        "/auth/password-change-prompt/dismiss",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    test_db.expire_all()
    updated_user = test_db.query(User).filter(User.id == user.id).first()
    assert updated_user is not None
    assert updated_user.should_prompt_password_change is False


def test_create_user_api_honors_submitted_password(client, test_db):
    school = _create_school(test_db, code="USER-PASS")
    admin_role = Role(name="admin")
    student_role = Role(name="student")
    test_db.add_all([admin_role, student_role])
    test_db.commit()

    admin_user = User(
        email="schooladmin2@example.com",
        school_id=school.id,
        first_name="School",
        last_name="Admin",
        must_change_password=False,
    )
    admin_user.set_password("AdminPass123!")
    test_db.add(admin_user)
    test_db.commit()

    test_db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
    test_db.commit()

    token = create_access_token({"sub": admin_user.email})
    submitted_password = "StudentPass123!"

    response = client.post(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "submitted.pass@example.com",
            "password": submitted_password,
            "first_name": "Submitted",
            "middle_name": "",
            "last_name": "Password",
            "roles": ["student"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["generated_temporary_password"] is None

    created_user = test_db.query(User).filter(User.email == "submitted.pass@example.com").first()
    assert created_user is not None
    assert created_user.should_prompt_password_change is True
    assert verify_password(submitted_password, created_user.password_hash)


def test_campus_admin_create_user_api_rejects_non_student_roles(client, test_db):
    school = _create_school(test_db, code="USER-ROLE-LOCK")
    school_it_role = Role(name="campus_admin")
    student_role = Role(name="student")
    test_db.add_all([school_it_role, student_role])
    test_db.commit()

    campus_admin = User(
        email="campus.admin@example.com",
        school_id=school.id,
        first_name="Campus",
        last_name="Admin",
        must_change_password=False,
    )
    campus_admin.set_password("CampusPass123!")
    test_db.add(campus_admin)
    test_db.commit()

    test_db.add(UserRole(user_id=campus_admin.id, role_id=school_it_role.id))
    test_db.commit()

    token = create_access_token({"sub": campus_admin.email})

    response = client.post(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "blocked.officer@example.com",
            "first_name": "Blocked",
            "middle_name": "",
            "last_name": "Officer",
            "roles": ["campus_admin"],
        },
    )

    assert response.status_code == 403
    assert "Campus Admin can only assign the student role from user management" in response.json()["detail"]


def test_campus_admin_cannot_update_roles_from_manage_users(client, test_db):
    school = _create_school(test_db, code="ROLE-UPDATE-LOCK")
    school_it_role = Role(name="campus_admin")
    student_role = Role(name="student")
    test_db.add_all([school_it_role, student_role])
    test_db.commit()

    campus_admin = User(
        email="campus.roles@example.com",
        school_id=school.id,
        first_name="Campus",
        last_name="Admin",
        must_change_password=False,
    )
    campus_admin.set_password("CampusPass123!")
    test_db.add(campus_admin)
    test_db.commit()

    target_user = User(
        email="student.target@example.com",
        school_id=school.id,
        first_name="Student",
        last_name="Target",
        must_change_password=False,
    )
    target_user.set_password("StudentPass123!")
    test_db.add(target_user)
    test_db.commit()

    test_db.add_all(
        [
            UserRole(user_id=campus_admin.id, role_id=school_it_role.id),
            UserRole(user_id=target_user.id, role_id=student_role.id),
        ]
    )
    test_db.commit()

    token = create_access_token({"sub": campus_admin.email})

    response = client.put(
        f"/users/{target_user.id}/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={"roles": ["student", "campus_admin"]},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Campus Admin cannot change user roles from Manage Users. "
        "Imported users stay students, and SSG access is managed from Manage SSG."
    )


def test_create_school_it_honors_submitted_password_and_sets_prompt_flag(client, test_db):
    admin_role = Role(name="admin")
    school_it_role = Role(name="school_IT")
    test_db.add_all([admin_role, school_it_role])
    test_db.commit()

    admin_user = User(
        email="platformadmin@example.com",
        first_name="Platform",
        last_name="Admin",
        must_change_password=False,
    )
    admin_user.set_password("AdminPass123!")
    test_db.add(admin_user)
    test_db.commit()

    test_db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
    test_db.commit()

    token = create_access_token({"sub": admin_user.email})
    submitted_password = "SchoolItPass123!"

    response = client.post(
        "/api/school/admin/create-school-it",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "school_name": "Prompt School",
            "primary_color": "#112233",
            "secondary_color": "#445566",
            "school_code": "PROMPT",
            "school_it_email": "school.it.prompt@example.com",
            "school_it_first_name": "School",
            "school_it_last_name": "IT",
            "school_it_password": submitted_password,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["generated_temporary_password"] is None

    created_user = test_db.query(User).filter(User.email == "school.it.prompt@example.com").first()
    assert created_user is not None
    assert created_user.should_prompt_password_change is True
    assert verify_password(submitted_password, created_user.password_hash)

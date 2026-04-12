"""Use: Tests sanctions API and service behavior.
Where to use: Use this when running `pytest` to check that this backend behavior still works.
Role: Test layer. It protects the app from regressions.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.core.security import create_access_token
from app.models import Role, School, User, UserRole
from app.models.attendance import Attendance as AttendanceModel
from app.models.department import Department
from app.models.event import Event as EventModel
from app.models.governance_hierarchy import (
    GovernanceMember,
    GovernanceMemberPermission,
    GovernancePermission,
    GovernanceUnit,
    GovernanceUnitType,
    PermissionCode,
)
from app.models.program import Program
from app.models.sanctions import EventSanctionConfig, SanctionComplianceStatus, SanctionRecord
from app.models.user import StudentProfile
from app.services import governance_hierarchy_service, sanctions_service
from app.workers import tasks as worker_tasks


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token({"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


def _create_role(test_db, *, name: str) -> Role:
    role = Role(name=name)
    test_db.add(role)
    test_db.commit()
    return role


def _create_school(test_db) -> School:
    school = School(
        name="Sanctions API School",
        school_name="Sanctions API School",
        school_code="SAN-API-001",
        address="School Address",
    )
    test_db.add(school)
    test_db.commit()
    return school


def _create_user(
    test_db,
    *,
    email: str,
    school_id: int,
    role_ids: list[int],
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
    for role_id in role_ids:
        test_db.add(UserRole(user_id=user.id, role_id=role_id))
    test_db.commit()
    test_db.refresh(user)
    return user


def _create_scope(test_db, *, school_id: int) -> tuple[Department, Program]:
    department = Department(name="Engineering", school_id=school_id)
    program = Program(name="BSCS", school_id=school_id)
    program.departments.append(department)
    test_db.add_all([department, program])
    test_db.commit()
    return department, program


def _create_event(
    test_db,
    *,
    school_id: int,
    name: str,
    department_ids: list[int] | None = None,
    program_ids: list[int] | None = None,
) -> EventModel:
    now = datetime.utcnow()
    event = EventModel(
        school_id=school_id,
        name=name,
        location="Main Hall",
        start_datetime=now - timedelta(hours=1),
        end_datetime=now + timedelta(hours=1),
    )
    if department_ids:
        event.departments = (
            test_db.query(Department).filter(Department.id.in_(department_ids)).all()
        )
    if program_ids:
        event.programs = (
            test_db.query(Program).filter(Program.id.in_(program_ids)).all()
        )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    return event


def _create_governance_membership(
    test_db,
    *,
    school_id: int,
    ssg_user_id: int,
    sg_user_id: int,
    org_user_id: int,
    department_id: int,
    program_id: int,
) -> tuple[GovernanceUnit, GovernanceUnit, GovernanceUnit]:
    ssg_unit = GovernanceUnit(
        school_id=school_id,
        unit_code="SSG-UNIT",
        unit_name="SSG Unit",
        unit_type=GovernanceUnitType.SSG,
    )
    test_db.add(ssg_unit)
    test_db.commit()
    test_db.refresh(ssg_unit)

    sg_unit = GovernanceUnit(
        school_id=school_id,
        unit_code="SG-ENG",
        unit_name="Engineering SG",
        unit_type=GovernanceUnitType.SG,
        parent_unit_id=ssg_unit.id,
        department_id=department_id,
    )
    test_db.add(sg_unit)
    test_db.commit()
    test_db.refresh(sg_unit)

    org_unit = GovernanceUnit(
        school_id=school_id,
        unit_code="ORG-BSCS",
        unit_name="BSCS Org",
        unit_type=GovernanceUnitType.ORG,
        parent_unit_id=sg_unit.id,
        department_id=department_id,
        program_id=program_id,
    )
    test_db.add(org_unit)
    test_db.commit()
    test_db.refresh(org_unit)

    test_db.add_all(
        [
            GovernanceMember(
                governance_unit_id=ssg_unit.id,
                user_id=ssg_user_id,
                assigned_by_user_id=ssg_user_id,
            ),
            GovernanceMember(
                governance_unit_id=sg_unit.id,
                user_id=sg_user_id,
                assigned_by_user_id=ssg_user_id,
            ),
            GovernanceMember(
                governance_unit_id=org_unit.id,
                user_id=org_user_id,
                assigned_by_user_id=sg_user_id,
            ),
        ]
    )
    test_db.commit()
    return ssg_unit, sg_unit, org_unit


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
        year_level=2,
    )
    test_db.add(profile)
    test_db.commit()
    test_db.refresh(profile)
    return profile


def _seed_permission_catalog(test_db) -> None:
    governance_hierarchy_service.ensure_permission_catalog(test_db)
    test_db.commit()


def _get_governance_member(
    test_db,
    *,
    governance_unit_id: int,
    user_id: int,
) -> GovernanceMember:
    member = (
        test_db.query(GovernanceMember)
        .filter(
            GovernanceMember.governance_unit_id == governance_unit_id,
            GovernanceMember.user_id == user_id,
            GovernanceMember.is_active.is_(True),
        )
        .first()
    )
    assert member is not None
    return member


def _grant_member_permissions(
    test_db,
    *,
    governance_member: GovernanceMember,
    permission_codes: list[PermissionCode],
    granted_by_user_id: int,
) -> None:
    if not permission_codes:
        return

    _seed_permission_catalog(test_db)

    permissions = (
        test_db.query(GovernancePermission)
        .filter(GovernancePermission.permission_code.in_(permission_codes))
        .all()
    )
    permission_by_code = {
        permission.permission_code: permission
        for permission in permissions
    }
    missing_codes = [code for code in permission_codes if code not in permission_by_code]
    assert not missing_codes

    existing_permission_ids = {
        row.permission_id
        for row in (
            test_db.query(GovernanceMemberPermission)
            .filter(GovernanceMemberPermission.governance_member_id == governance_member.id)
            .all()
        )
    }

    for permission_code in permission_codes:
        permission = permission_by_code[permission_code]
        if permission.id in existing_permission_ids:
            continue
        test_db.add(
            GovernanceMemberPermission(
                governance_member_id=governance_member.id,
                permission_id=permission.id,
                granted_by_user_id=granted_by_user_id,
            )
        )

    test_db.commit()


def test_sanctions_config_access_and_scope_rules(client, test_db):
    school = _create_school(test_db)
    ssg_role = _create_role(test_db, name="ssg")
    sg_role = _create_role(test_db, name="sg")
    org_role = _create_role(test_db, name="org")

    ssg_user = _create_user(
        test_db,
        email="ssg.config@example.com",
        school_id=school.id,
        role_ids=[ssg_role.id],
    )
    sg_user = _create_user(
        test_db,
        email="sg.config@example.com",
        school_id=school.id,
        role_ids=[sg_role.id],
    )
    org_user = _create_user(
        test_db,
        email="org.config@example.com",
        school_id=school.id,
        role_ids=[org_role.id],
    )

    department, program = _create_scope(test_db, school_id=school.id)
    ssg_unit, _sg_unit, _org_unit = _create_governance_membership(
        test_db,
        school_id=school.id,
        ssg_user_id=ssg_user.id,
        sg_user_id=sg_user.id,
        org_user_id=org_user.id,
        department_id=department.id,
        program_id=program.id,
    )
    ssg_member = _get_governance_member(
        test_db,
        governance_unit_id=ssg_unit.id,
        user_id=ssg_user.id,
    )
    _grant_member_permissions(
        test_db,
        governance_member=ssg_member,
        permission_codes=[PermissionCode.CONFIGURE_EVENT_SANCTIONS],
        granted_by_user_id=ssg_user.id,
    )

    ssg_event = _create_event(test_db, school_id=school.id, name="SSG Event")
    sg_event = _create_event(
        test_db,
        school_id=school.id,
        name="SG Event",
        department_ids=[department.id],
    )

    put_response = client.put(
        f"/api/sanctions/events/{ssg_event.id}/config",
        headers=_auth_headers(ssg_user),
        json={
            "sanctions_enabled": True,
            "items": [
                {"item_code": "community_service", "item_name": "Community Service"},
                {"item_code": "reflection", "item_name": "Reflection Paper"},
            ],
        },
    )
    assert put_response.status_code == 200
    assert put_response.json()["sanctions_enabled"] is True
    assert len(put_response.json()["items"]) == 2

    get_response = client.get(
        f"/api/sanctions/events/{ssg_event.id}/config",
        headers=_auth_headers(ssg_user),
    )
    assert get_response.status_code == 200
    assert get_response.json()["event_id"] == ssg_event.id

    forbidden_response = client.put(
        f"/api/sanctions/events/{sg_event.id}/config",
        headers=_auth_headers(ssg_user),
        json={
            "sanctions_enabled": True,
            "items": [{"item_code": "notice", "item_name": "Notice"}],
        },
    )
    assert forbidden_response.status_code == 403


def test_sg_delegation_allows_scoped_read_and_approve(client, test_db):
    school = _create_school(test_db)
    ssg_role = _create_role(test_db, name="ssg")
    sg_role = _create_role(test_db, name="sg")
    student_role = _create_role(test_db, name="student")

    ssg_user = _create_user(
        test_db,
        email="ssg.delegate@example.com",
        school_id=school.id,
        role_ids=[ssg_role.id],
    )
    sg_user = _create_user(
        test_db,
        email="sg.delegate@example.com",
        school_id=school.id,
        role_ids=[sg_role.id],
    )
    student_user = _create_user(
        test_db,
        email="student.delegate@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )
    department, program = _create_scope(test_db, school_id=school.id)
    ssg_unit, sg_unit, _org_unit = _create_governance_membership(
        test_db,
        school_id=school.id,
        ssg_user_id=ssg_user.id,
        sg_user_id=sg_user.id,
        org_user_id=sg_user.id,
        department_id=department.id,
        program_id=program.id,
    )
    ssg_member = _get_governance_member(
        test_db,
        governance_unit_id=ssg_unit.id,
        user_id=ssg_user.id,
    )
    sg_member = _get_governance_member(
        test_db,
        governance_unit_id=sg_unit.id,
        user_id=sg_user.id,
    )
    _grant_member_permissions(
        test_db,
        governance_member=ssg_member,
        permission_codes=[PermissionCode.CONFIGURE_EVENT_SANCTIONS],
        granted_by_user_id=ssg_user.id,
    )
    _grant_member_permissions(
        test_db,
        governance_member=sg_member,
        permission_codes=[
            PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST,
            PermissionCode.APPROVE_SANCTION_COMPLIANCE,
        ],
        granted_by_user_id=ssg_user.id,
    )
    student_profile = _create_student_profile(
        test_db,
        user_id=student_user.id,
        school_id=school.id,
        student_id="STU-001",
        department_id=department.id,
        program_id=program.id,
    )
    event = _create_event(test_db, school_id=school.id, name="Campus Event")

    config = EventSanctionConfig(
        school_id=school.id,
        event_id=event.id,
        sanctions_enabled=True,
        item_definitions_json=[{"item_code": "notice", "item_name": "Submit Explanation Letter"}],
        created_by_user_id=ssg_user.id,
    )
    test_db.add(config)
    test_db.commit()
    test_db.refresh(config)

    record = SanctionRecord(
        school_id=school.id,
        event_id=event.id,
        sanction_config_id=config.id,
        student_profile_id=student_profile.id,
        status=SanctionComplianceStatus.PENDING,
        assigned_by_user_id=ssg_user.id,
    )
    test_db.add(record)
    test_db.commit()

    no_access_before = client.get(
        f"/api/sanctions/events/{event.id}/students",
        headers=_auth_headers(sg_user),
    )
    assert no_access_before.status_code == 404

    set_delegation = client.put(
        f"/api/sanctions/events/{event.id}/delegation",
        headers=_auth_headers(ssg_user),
        json={
            "delegations": [
                {
                    "delegated_to_governance_unit_id": sg_unit.id,
                    "scope_type": "unit",
                    "is_active": True,
                }
            ]
        },
    )
    assert set_delegation.status_code == 200
    assert len(set_delegation.json()) == 1

    visible_after = client.get(
        f"/api/sanctions/events/{event.id}/students",
        headers=_auth_headers(sg_user),
    )
    assert visible_after.status_code == 200
    assert visible_after.json()["total"] == 1

    approve_response = client.post(
        f"/api/sanctions/events/{event.id}/students/{student_user.id}/approve",
        headers=_auth_headers(sg_user),
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "complied"


def test_sanctions_routes_require_governance_permission_grants(client, test_db):
    school = _create_school(test_db)
    ssg_role = _create_role(test_db, name="ssg")
    sg_role = _create_role(test_db, name="sg")
    org_role = _create_role(test_db, name="org")

    ssg_user = _create_user(
        test_db,
        email="ssg.permission@example.com",
        school_id=school.id,
        role_ids=[ssg_role.id],
    )
    sg_user = _create_user(
        test_db,
        email="sg.permission@example.com",
        school_id=school.id,
        role_ids=[sg_role.id],
    )
    org_user = _create_user(
        test_db,
        email="org.permission@example.com",
        school_id=school.id,
        role_ids=[org_role.id],
    )

    department, program = _create_scope(test_db, school_id=school.id)
    ssg_unit, _sg_unit, _org_unit = _create_governance_membership(
        test_db,
        school_id=school.id,
        ssg_user_id=ssg_user.id,
        sg_user_id=sg_user.id,
        org_user_id=org_user.id,
        department_id=department.id,
        program_id=program.id,
    )
    event = _create_event(test_db, school_id=school.id, name="Permission Guard Event")

    forbidden_response = client.get(
        f"/api/sanctions/events/{event.id}/config",
        headers=_auth_headers(ssg_user),
    )
    assert forbidden_response.status_code == 403

    ssg_member = _get_governance_member(
        test_db,
        governance_unit_id=ssg_unit.id,
        user_id=ssg_user.id,
    )
    _grant_member_permissions(
        test_db,
        governance_member=ssg_member,
        permission_codes=[PermissionCode.CONFIGURE_EVENT_SANCTIONS],
        granted_by_user_id=ssg_user.id,
    )

    allowed_response = client.get(
        f"/api/sanctions/events/{event.id}/config",
        headers=_auth_headers(ssg_user),
    )
    assert allowed_response.status_code == 200
    assert allowed_response.json()["event_id"] == event.id


def test_students_me_returns_only_current_student_sanctions(client, test_db):
    school = _create_school(test_db)
    student_role = _create_role(test_db, name="student")
    ssg_role = _create_role(test_db, name="ssg")

    ssg_user = _create_user(
        test_db,
        email="ssg.me@example.com",
        school_id=school.id,
        role_ids=[ssg_role.id],
    )
    student_a = _create_user(
        test_db,
        email="student.a@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )
    student_b = _create_user(
        test_db,
        email="student.b@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )
    department, program = _create_scope(test_db, school_id=school.id)
    profile_a = _create_student_profile(
        test_db,
        user_id=student_a.id,
        school_id=school.id,
        student_id="A-001",
        department_id=department.id,
        program_id=program.id,
    )
    profile_b = _create_student_profile(
        test_db,
        user_id=student_b.id,
        school_id=school.id,
        student_id="B-001",
        department_id=department.id,
        program_id=program.id,
    )
    event = _create_event(test_db, school_id=school.id, name="Student Event")
    config = EventSanctionConfig(
        school_id=school.id,
        event_id=event.id,
        sanctions_enabled=True,
        item_definitions_json=[{"item_code": "notice", "item_name": "Notice"}],
        created_by_user_id=ssg_user.id,
    )
    test_db.add(config)
    test_db.commit()

    test_db.add_all(
        [
            SanctionRecord(
                school_id=school.id,
                event_id=event.id,
                sanction_config_id=config.id,
                student_profile_id=profile_a.id,
                status=SanctionComplianceStatus.PENDING,
                assigned_by_user_id=ssg_user.id,
            ),
            SanctionRecord(
                school_id=school.id,
                event_id=event.id,
                sanction_config_id=config.id,
                student_profile_id=profile_b.id,
                status=SanctionComplianceStatus.PENDING,
                assigned_by_user_id=ssg_user.id,
            ),
        ]
    )
    test_db.commit()

    response = client.get(
        "/api/sanctions/students/me",
        headers=_auth_headers(student_a),
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["student"]["user_id"] == student_a.id


def test_generate_sanctions_for_completed_event_creates_records_and_is_idempotent(
    test_db,
    monkeypatch,
):
    school = _create_school(test_db)
    ssg_role = _create_role(test_db, name="ssg")
    student_role = _create_role(test_db, name="student")
    ssg_user = _create_user(
        test_db,
        email="ssg.generate@example.com",
        school_id=school.id,
        role_ids=[ssg_role.id],
    )
    student_user = _create_user(
        test_db,
        email="student.generate@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )
    department, program = _create_scope(test_db, school_id=school.id)
    student_profile = _create_student_profile(
        test_db,
        user_id=student_user.id,
        school_id=school.id,
        student_id="GEN-001",
        department_id=department.id,
        program_id=program.id,
    )
    event = _create_event(test_db, school_id=school.id, name="Generate Event")
    event.end_datetime = datetime.utcnow() - timedelta(minutes=1)
    test_db.commit()

    config = EventSanctionConfig(
        school_id=school.id,
        event_id=event.id,
        sanctions_enabled=True,
        item_definitions_json=[
            {"item_code": "community_service", "item_name": "Community Service"},
            {"item_code": "reflection", "item_name": "Reflection Paper"},
        ],
        created_by_user_id=ssg_user.id,
    )
    test_db.add(config)
    test_db.commit()

    attendance = AttendanceModel(
        student_id=student_profile.id,
        event_id=event.id,
        method="manual",
        status="absent",
    )
    test_db.add(attendance)
    test_db.commit()

    queued_args: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_apply_async(*, args, kwargs, retry):
        assert retry is False
        queued_args.append((tuple(args), dict(kwargs)))

    monkeypatch.setattr(
        worker_tasks.send_sanction_notification_email,
        "apply_async",
        fake_apply_async,
    )

    summary_first = sanctions_service.generate_sanctions_for_completed_event(test_db, event)
    test_db.commit()
    assert summary_first["sanction_records_created"] == 1
    assert summary_first["sanction_notification_emails_queued"] == 1
    assert len(queued_args) == 1

    summary_second = sanctions_service.generate_sanctions_for_completed_event(test_db, event)
    test_db.commit()
    assert summary_second["sanction_records_created"] == 0
    assert summary_second["sanction_notification_emails_queued"] == 0

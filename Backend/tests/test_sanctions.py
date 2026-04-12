"""Use: Tests sanctions management scenarios requested for Step 8 coverage.
Where to use: Use this when running `pytest` to validate sanctions scope, delegation, approval, and student isolation flows.
Role: Test layer. It protects sanctions behavior from regressions.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db
from app.main import app
from app.models import Base
from app.models.attendance import Attendance as AttendanceModel
from app.models.department import Department
from app.models.event import EventStatus as ModelEventStatus
from app.models.governance_hierarchy import PermissionCode
from app.models.program import Program
from app.models.sanctions import (
    EventSanctionConfig,
    SanctionComplianceHistory,
    SanctionComplianceStatus,
    SanctionItem,
    SanctionItemStatus,
    SanctionRecord,
)
from app.services.event_workflow_status import sync_event_workflow_status
from app.tests.test_sanctions_api import (
    _auth_headers,
    _create_event,
    _create_governance_membership,
    _create_role,
    _create_school,
    _create_scope,
    _create_student_profile,
    _create_user,
    _get_governance_member,
    _grant_member_permissions,
)
from app.workers import tasks as worker_tasks


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db(test_engine, test_session_factory) -> Generator[Session, None, None]:
    db = test_session_factory()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        with test_engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())


@pytest.fixture(scope="function")
def client(test_session_factory) -> Generator[TestClient, None, None]:
    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


def _create_department(test_db, *, school_id: int, name: str) -> Department:
    department = Department(name=name, school_id=school_id)
    test_db.add(department)
    test_db.commit()
    test_db.refresh(department)
    return department


def _create_program(
    test_db,
    *,
    school_id: int,
    department: Department,
    name: str,
) -> Program:
    program = Program(name=name, school_id=school_id)
    program.departments.append(department)
    test_db.add(program)
    test_db.commit()
    test_db.refresh(program)
    return program


def _create_sanction_config(
    test_db,
    *,
    school_id: int,
    event_id: int,
    created_by_user_id: int,
    item_names: list[str] | None = None,
) -> EventSanctionConfig:
    config_items = []
    for idx, item_name in enumerate(item_names or ["Submit Letter"], start=1):
        config_items.append(
            {
                "item_code": f"item_{idx}",
                "item_name": item_name,
            }
        )
    config = EventSanctionConfig(
        school_id=school_id,
        event_id=event_id,
        sanctions_enabled=True,
        item_definitions_json=config_items,
        created_by_user_id=created_by_user_id,
    )
    test_db.add(config)
    test_db.commit()
    test_db.refresh(config)
    return config


def _create_sanction_record(
    test_db,
    *,
    school_id: int,
    event_id: int,
    sanction_config_id: int | None,
    student_profile_id: int,
    assigned_by_user_id: int,
    status: SanctionComplianceStatus = SanctionComplianceStatus.PENDING,
) -> SanctionRecord:
    record = SanctionRecord(
        school_id=school_id,
        event_id=event_id,
        sanction_config_id=sanction_config_id,
        student_profile_id=student_profile_id,
        status=status,
        assigned_by_user_id=assigned_by_user_id,
    )
    test_db.add(record)
    test_db.commit()
    test_db.refresh(record)
    return record


def _add_sanction_items(
    test_db,
    *,
    sanction_record_id: int,
    item_names: list[str],
) -> None:
    for idx, item_name in enumerate(item_names, start=1):
        test_db.add(
            SanctionItem(
                sanction_record_id=sanction_record_id,
                item_code=f"item_{idx}",
                item_name=item_name,
                status=SanctionItemStatus.PENDING,
            )
        )
    test_db.commit()


def test_sanction_record_auto_generation_after_event_completion(test_db, monkeypatch):
    school = _create_school(test_db)
    ssg_role = _create_role(test_db, name="ssg")
    student_role = _create_role(test_db, name="student")

    ssg_user = _create_user(
        test_db,
        email="ssg.step8.autogen@example.com",
        school_id=school.id,
        role_ids=[ssg_role.id],
    )
    student_user = _create_user(
        test_db,
        email="student.step8.autogen@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )
    department, program = _create_scope(test_db, school_id=school.id)
    student_profile = _create_student_profile(
        test_db,
        user_id=student_user.id,
        school_id=school.id,
        student_id="STEP8-AUTO-001",
        department_id=department.id,
        program_id=program.id,
    )

    event = _create_event(test_db, school_id=school.id, name="Step 8 Auto-Generation Event")
    event.status = ModelEventStatus.ONGOING
    event.end_datetime = datetime.utcnow() - timedelta(minutes=30)
    test_db.commit()

    _create_sanction_config(
        test_db,
        school_id=school.id,
        event_id=event.id,
        created_by_user_id=ssg_user.id,
        item_names=["Community Service", "Reflection Paper"],
    )
    test_db.add(
        AttendanceModel(
            student_id=student_profile.id,
            event_id=event.id,
            method="manual",
            status="absent",
        )
    )
    test_db.commit()

    queued_calls: list[tuple[tuple[object, ...], dict[str, object], bool]] = []

    def fake_apply_async(*, args, kwargs, retry):
        queued_calls.append((tuple(args), dict(kwargs), retry))

    monkeypatch.setattr(
        worker_tasks.send_sanction_notification_email,
        "apply_async",
        fake_apply_async,
    )

    result = sync_event_workflow_status(
        test_db,
        event,
        current_time=datetime.utcnow(),
        completion_finalizer=lambda _db, _event: {
            "created_absent": 0,
            "marked_absent_no_timeout": 0,
        },
    )
    test_db.commit()

    assert result.attendance_finalized is True
    assert result.finalization_summary is not None
    assert result.finalization_summary["sanction_records_created"] == 1
    assert result.finalization_summary["sanction_notification_emails_queued"] == 1
    assert len(queued_calls) == 1

    created_record = (
        test_db.query(SanctionRecord)
        .filter(
            SanctionRecord.school_id == school.id,
            SanctionRecord.event_id == event.id,
            SanctionRecord.student_profile_id == student_profile.id,
        )
        .first()
    )
    assert created_record is not None
    assert len(created_record.items) == 2

    second_result = sync_event_workflow_status(
        test_db,
        event,
        current_time=datetime.utcnow(),
        completion_finalizer=lambda _db, _event: {
            "created_absent": 0,
            "marked_absent_no_timeout": 0,
        },
    )
    test_db.commit()

    assert second_result.attendance_finalized is False
    assert (
        test_db.query(SanctionRecord)
        .filter(SanctionRecord.school_id == school.id, SanctionRecord.event_id == event.id)
        .count()
        == 1
    )


def test_scope_enforcement_ssg_sg_org_visibility(client, test_db):
    school = _create_school(test_db)
    ssg_role = _create_role(test_db, name="ssg")
    sg_role = _create_role(test_db, name="sg")
    org_role = _create_role(test_db, name="org")
    student_role = _create_role(test_db, name="student")

    ssg_user = _create_user(
        test_db,
        email="ssg.step8.scope@example.com",
        school_id=school.id,
        role_ids=[ssg_role.id],
    )
    sg_user = _create_user(
        test_db,
        email="sg.step8.scope@example.com",
        school_id=school.id,
        role_ids=[sg_role.id],
    )
    org_user = _create_user(
        test_db,
        email="org.step8.scope@example.com",
        school_id=school.id,
        role_ids=[org_role.id],
    )
    student_one = _create_user(
        test_db,
        email="student.one.step8.scope@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )
    student_two = _create_user(
        test_db,
        email="student.two.step8.scope@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )
    student_three = _create_user(
        test_db,
        email="student.three.step8.scope@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )

    department_one, program_one = _create_scope(test_db, school_id=school.id)
    program_two = _create_program(
        test_db,
        school_id=school.id,
        department=department_one,
        name="BSIT",
    )
    department_two = _create_department(test_db, school_id=school.id, name="Business")
    program_three = _create_program(
        test_db,
        school_id=school.id,
        department=department_two,
        name="BSBA",
    )

    ssg_unit, sg_unit, org_unit = _create_governance_membership(
        test_db,
        school_id=school.id,
        ssg_user_id=ssg_user.id,
        sg_user_id=sg_user.id,
        org_user_id=org_user.id,
        department_id=department_one.id,
        program_id=program_one.id,
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
    org_member = _get_governance_member(
        test_db,
        governance_unit_id=org_unit.id,
        user_id=org_user.id,
    )
    _grant_member_permissions(
        test_db,
        governance_member=ssg_member,
        permission_codes=[
            PermissionCode.CONFIGURE_EVENT_SANCTIONS,
            PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST,
        ],
        granted_by_user_id=ssg_user.id,
    )
    _grant_member_permissions(
        test_db,
        governance_member=sg_member,
        permission_codes=[
            PermissionCode.CONFIGURE_EVENT_SANCTIONS,
            PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST,
        ],
        granted_by_user_id=ssg_user.id,
    )
    _grant_member_permissions(
        test_db,
        governance_member=org_member,
        permission_codes=[PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST],
        granted_by_user_id=sg_user.id,
    )

    profile_one = _create_student_profile(
        test_db,
        user_id=student_one.id,
        school_id=school.id,
        student_id="STEP8-SCOPE-001",
        department_id=department_one.id,
        program_id=program_one.id,
    )
    profile_two = _create_student_profile(
        test_db,
        user_id=student_two.id,
        school_id=school.id,
        student_id="STEP8-SCOPE-002",
        department_id=department_one.id,
        program_id=program_two.id,
    )
    profile_three = _create_student_profile(
        test_db,
        user_id=student_three.id,
        school_id=school.id,
        student_id="STEP8-SCOPE-003",
        department_id=department_two.id,
        program_id=program_three.id,
    )

    ssg_event = _create_event(test_db, school_id=school.id, name="Step 8 SSG Scope Event")
    ssg_config = _create_sanction_config(
        test_db,
        school_id=school.id,
        event_id=ssg_event.id,
        created_by_user_id=ssg_user.id,
        item_names=["Write Explanation"],
    )
    _create_sanction_record(
        test_db,
        school_id=school.id,
        event_id=ssg_event.id,
        sanction_config_id=ssg_config.id,
        student_profile_id=profile_one.id,
        assigned_by_user_id=ssg_user.id,
    )
    _create_sanction_record(
        test_db,
        school_id=school.id,
        event_id=ssg_event.id,
        sanction_config_id=ssg_config.id,
        student_profile_id=profile_three.id,
        assigned_by_user_id=ssg_user.id,
    )

    ssg_list = client.get(
        f"/api/sanctions/events/{ssg_event.id}/students",
        headers=_auth_headers(ssg_user),
    )
    assert ssg_list.status_code == 200
    assert ssg_list.json()["total"] == 2

    sg_before_delegation = client.get(
        f"/api/sanctions/events/{ssg_event.id}/students",
        headers=_auth_headers(sg_user),
    )
    assert sg_before_delegation.status_code == 404

    delegate_to_sg = client.put(
        f"/api/sanctions/events/{ssg_event.id}/delegation",
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
    assert delegate_to_sg.status_code == 200

    sg_after_delegation = client.get(
        f"/api/sanctions/events/{ssg_event.id}/students",
        headers=_auth_headers(sg_user),
    )
    assert sg_after_delegation.status_code == 200
    assert sg_after_delegation.json()["total"] == 1
    assert {
        item["student"]["user_id"]
        for item in sg_after_delegation.json()["items"]
    } == {student_one.id}

    org_on_ssg_event = client.get(
        f"/api/sanctions/events/{ssg_event.id}/students",
        headers=_auth_headers(org_user),
    )
    assert org_on_ssg_event.status_code == 404

    sg_event = _create_event(
        test_db,
        school_id=school.id,
        name="Step 8 SG Scope Event",
        department_ids=[department_one.id],
    )
    sg_config = _create_sanction_config(
        test_db,
        school_id=school.id,
        event_id=sg_event.id,
        created_by_user_id=sg_user.id,
        item_names=["Community Service"],
    )
    _create_sanction_record(
        test_db,
        school_id=school.id,
        event_id=sg_event.id,
        sanction_config_id=sg_config.id,
        student_profile_id=profile_one.id,
        assigned_by_user_id=sg_user.id,
    )
    _create_sanction_record(
        test_db,
        school_id=school.id,
        event_id=sg_event.id,
        sanction_config_id=sg_config.id,
        student_profile_id=profile_two.id,
        assigned_by_user_id=sg_user.id,
    )

    sg_owned_event = client.get(
        f"/api/sanctions/events/{sg_event.id}/students",
        headers=_auth_headers(sg_user),
    )
    assert sg_owned_event.status_code == 200
    assert sg_owned_event.json()["total"] == 2

    org_before_delegation = client.get(
        f"/api/sanctions/events/{sg_event.id}/students",
        headers=_auth_headers(org_user),
    )
    assert org_before_delegation.status_code == 404

    delegate_to_org = client.put(
        f"/api/sanctions/events/{sg_event.id}/delegation",
        headers=_auth_headers(sg_user),
        json={
            "delegations": [
                {
                    "delegated_to_governance_unit_id": org_unit.id,
                    "scope_type": "unit",
                    "is_active": True,
                }
            ]
        },
    )
    assert delegate_to_org.status_code == 200

    org_after_delegation = client.get(
        f"/api/sanctions/events/{sg_event.id}/students",
        headers=_auth_headers(org_user),
    )
    assert org_after_delegation.status_code == 200
    assert org_after_delegation.json()["total"] == 1
    assert {
        item["student"]["user_id"]
        for item in org_after_delegation.json()["items"]
    } == {student_one.id}


def test_delegation_grant_changes_event_access(client, test_db):
    school = _create_school(test_db)
    ssg_role = _create_role(test_db, name="ssg")
    sg_role = _create_role(test_db, name="sg")
    student_role = _create_role(test_db, name="student")

    ssg_user = _create_user(
        test_db,
        email="ssg.step8.delegation@example.com",
        school_id=school.id,
        role_ids=[ssg_role.id],
    )
    sg_user = _create_user(
        test_db,
        email="sg.step8.delegation@example.com",
        school_id=school.id,
        role_ids=[sg_role.id],
    )
    student_user = _create_user(
        test_db,
        email="student.step8.delegation@example.com",
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
        permission_codes=[PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST],
        granted_by_user_id=ssg_user.id,
    )

    student_profile = _create_student_profile(
        test_db,
        user_id=student_user.id,
        school_id=school.id,
        student_id="STEP8-DEL-001",
        department_id=department.id,
        program_id=program.id,
    )
    event = _create_event(test_db, school_id=school.id, name="Step 8 Delegation Event")
    config = _create_sanction_config(
        test_db,
        school_id=school.id,
        event_id=event.id,
        created_by_user_id=ssg_user.id,
        item_names=["Submit Reflection"],
    )
    _create_sanction_record(
        test_db,
        school_id=school.id,
        event_id=event.id,
        sanction_config_id=config.id,
        student_profile_id=student_profile.id,
        assigned_by_user_id=ssg_user.id,
    )

    before = client.get(
        f"/api/sanctions/events/{event.id}/students",
        headers=_auth_headers(sg_user),
    )
    assert before.status_code == 404

    delegated = client.put(
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
    assert delegated.status_code == 200
    assert len(delegated.json()) == 1

    after = client.get(
        f"/api/sanctions/events/{event.id}/students",
        headers=_auth_headers(sg_user),
    )
    assert after.status_code == 200
    assert after.json()["total"] == 1


def test_approve_action_creates_compliance_history(client, test_db, monkeypatch):
    school = _create_school(test_db)
    ssg_role = _create_role(test_db, name="ssg")
    sg_role = _create_role(test_db, name="sg")
    org_role = _create_role(test_db, name="org")
    student_role = _create_role(test_db, name="student")

    ssg_user = _create_user(
        test_db,
        email="ssg.step8.approve@example.com",
        school_id=school.id,
        role_ids=[ssg_role.id],
    )
    sg_user = _create_user(
        test_db,
        email="sg.step8.approve@example.com",
        school_id=school.id,
        role_ids=[sg_role.id],
    )
    org_user = _create_user(
        test_db,
        email="org.step8.approve@example.com",
        school_id=school.id,
        role_ids=[org_role.id],
    )
    student_user = _create_user(
        test_db,
        email="student.step8.approve@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
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
        permission_codes=[PermissionCode.APPROVE_SANCTION_COMPLIANCE],
        granted_by_user_id=ssg_user.id,
    )

    student_profile = _create_student_profile(
        test_db,
        user_id=student_user.id,
        school_id=school.id,
        student_id="STEP8-APPROVE-001",
        department_id=department.id,
        program_id=program.id,
    )
    event = _create_event(test_db, school_id=school.id, name="Step 8 Approval Event")
    config = _create_sanction_config(
        test_db,
        school_id=school.id,
        event_id=event.id,
        created_by_user_id=ssg_user.id,
        item_names=["Community Service", "Reflection Paper"],
    )
    record = _create_sanction_record(
        test_db,
        school_id=school.id,
        event_id=event.id,
        sanction_config_id=config.id,
        student_profile_id=student_profile.id,
        assigned_by_user_id=ssg_user.id,
    )
    _add_sanction_items(
        test_db,
        sanction_record_id=record.id,
        item_names=["Community Service", "Reflection Paper"],
    )

    queued_calls: list[tuple[tuple[object, ...], dict[str, object], bool]] = []

    def fake_apply_async(*, args, kwargs, retry):
        queued_calls.append((tuple(args), dict(kwargs), retry))

    monkeypatch.setattr(
        worker_tasks.send_sanction_compliance_confirmation_email,
        "apply_async",
        fake_apply_async,
    )

    approve_response = client.post(
        f"/api/sanctions/events/{event.id}/students/{student_user.id}/approve",
        headers=_auth_headers(ssg_user),
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "complied"
    assert len(queued_calls) == 1

    refreshed_record = test_db.query(SanctionRecord).filter(SanctionRecord.id == record.id).first()
    assert refreshed_record is not None
    assert refreshed_record.status == SanctionComplianceStatus.COMPLIED
    assert refreshed_record.complied_at is not None
    assert all(item.status == SanctionItemStatus.COMPLIED for item in refreshed_record.items)

    history_rows = (
        test_db.query(SanctionComplianceHistory)
        .filter(SanctionComplianceHistory.sanction_record_id == record.id)
        .all()
    )
    assert len(history_rows) == 2
    assert all(row.sanction_item_id is not None for row in history_rows)

    second_approve_response = client.post(
        f"/api/sanctions/events/{event.id}/students/{student_user.id}/approve",
        headers=_auth_headers(ssg_user),
    )
    assert second_approve_response.status_code == 200
    assert (
        test_db.query(SanctionComplianceHistory)
        .filter(SanctionComplianceHistory.sanction_record_id == record.id)
        .count()
        == 2
    )
    assert len(queued_calls) == 1


def test_student_personal_view_isolation(client, test_db):
    school = _create_school(test_db)
    ssg_role = _create_role(test_db, name="ssg")
    student_role = _create_role(test_db, name="student")

    ssg_user = _create_user(
        test_db,
        email="ssg.step8.studentview@example.com",
        school_id=school.id,
        role_ids=[ssg_role.id],
    )
    student_a = _create_user(
        test_db,
        email="student.a.step8.studentview@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )
    student_b = _create_user(
        test_db,
        email="student.b.step8.studentview@example.com",
        school_id=school.id,
        role_ids=[student_role.id],
    )

    department, program = _create_scope(test_db, school_id=school.id)
    profile_a = _create_student_profile(
        test_db,
        user_id=student_a.id,
        school_id=school.id,
        student_id="STEP8-ME-001",
        department_id=department.id,
        program_id=program.id,
    )
    profile_b = _create_student_profile(
        test_db,
        user_id=student_b.id,
        school_id=school.id,
        student_id="STEP8-ME-002",
        department_id=department.id,
        program_id=program.id,
    )
    event = _create_event(test_db, school_id=school.id, name="Step 8 Student View Event")
    config = _create_sanction_config(
        test_db,
        school_id=school.id,
        event_id=event.id,
        created_by_user_id=ssg_user.id,
        item_names=["Warning Notice"],
    )
    _create_sanction_record(
        test_db,
        school_id=school.id,
        event_id=event.id,
        sanction_config_id=config.id,
        student_profile_id=profile_a.id,
        assigned_by_user_id=ssg_user.id,
    )
    _create_sanction_record(
        test_db,
        school_id=school.id,
        event_id=event.id,
        sanction_config_id=config.id,
        student_profile_id=profile_b.id,
        assigned_by_user_id=ssg_user.id,
    )

    student_a_response = client.get(
        "/api/sanctions/students/me",
        headers=_auth_headers(student_a),
    )
    assert student_a_response.status_code == 200
    assert len(student_a_response.json()) == 1
    assert student_a_response.json()[0]["student"]["user_id"] == student_a.id

    student_b_response = client.get(
        "/api/sanctions/students/me",
        headers=_auth_headers(student_b),
    )
    assert student_b_response.status_code == 200
    assert len(student_b_response.json()) == 1
    assert student_b_response.json()[0]["student"]["user_id"] == student_b.id

    forbidden_detail = client.get(
        f"/api/sanctions/students/{student_b.id}",
        headers=_auth_headers(student_a),
    )
    assert forbidden_detail.status_code == 403

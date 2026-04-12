"""Use: Tests sanctions data models and schema-level constraints.
Where to use: Use this when running `pytest` to verify sanctions table behavior.
Role: Test layer. It protects sanctions persistence behavior from regressions.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    Base,
    ClearanceDeadline,
    Event,
    EventSanctionConfig,
    GovernanceUnit,
    SanctionDelegation,
    SanctionItem,
    SanctionRecord,
    School,
    StudentProfile,
    User,
)
from app.models.governance_hierarchy import GovernanceUnitType
from app.models.sanctions import ClearanceDeadlineStatus


def _seed_sanctions_context(test_db):
    school = School(
        name="Sanctions Test School",
        school_name="Sanctions Test School",
        school_code="STS-001",
        address="Campus Road",
    )
    test_db.add(school)
    test_db.commit()
    test_db.refresh(school)

    actor = User(
        email="sanctions.actor@example.com",
        school_id=school.id,
        first_name="Actor",
        last_name="User",
    )
    actor.set_password("SecurePass123!")
    test_db.add(actor)
    test_db.commit()
    test_db.refresh(actor)

    student_user = User(
        email="sanctions.student@example.com",
        school_id=school.id,
        first_name="Student",
        last_name="User",
    )
    student_user.set_password("SecurePass123!")
    test_db.add(student_user)
    test_db.commit()
    test_db.refresh(student_user)

    student_profile = StudentProfile(
        user_id=student_user.id,
        school_id=school.id,
        student_id="2026-0001",
    )
    test_db.add(student_profile)
    test_db.commit()
    test_db.refresh(student_profile)

    now = datetime.utcnow()
    event = Event(
        school_id=school.id,
        name="Sanctioned Event",
        location="Main Hall",
        start_datetime=now,
        end_datetime=now + timedelta(hours=2),
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    governance_unit = GovernanceUnit(
        school_id=school.id,
        unit_code="SSG-UNIT",
        unit_name="Student Supreme Government",
        unit_type=GovernanceUnitType.SSG,
    )
    test_db.add(governance_unit)
    test_db.commit()
    test_db.refresh(governance_unit)

    return {
        "school": school,
        "actor": actor,
        "student_profile": student_profile,
        "event": event,
        "governance_unit": governance_unit,
    }


def test_sanctions_tables_are_registered_in_metadata():
    expected_tables = {
        "event_sanction_configs",
        "sanction_records",
        "sanction_items",
        "sanction_delegations",
        "sanction_compliance_history",
        "clearance_deadlines",
    }
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))


def test_event_sanction_config_is_unique_per_event(test_db):
    context = _seed_sanctions_context(test_db)

    config = EventSanctionConfig(
        school_id=context["school"].id,
        event_id=context["event"].id,
        sanctions_enabled=True,
        item_definitions_json=[{"code": "community_service", "name": "Community Service"}],
        created_by_user_id=context["actor"].id,
    )
    test_db.add(config)
    test_db.commit()

    duplicate = EventSanctionConfig(
        school_id=context["school"].id,
        event_id=context["event"].id,
        sanctions_enabled=True,
        item_definitions_json=[{"code": "written_report", "name": "Written Report"}],
        created_by_user_id=context["actor"].id,
    )
    test_db.add(duplicate)

    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()


def test_sanction_record_is_unique_per_event_and_student(test_db):
    context = _seed_sanctions_context(test_db)

    config = EventSanctionConfig(
        school_id=context["school"].id,
        event_id=context["event"].id,
        sanctions_enabled=True,
        item_definitions_json=[{"code": "community_service", "name": "Community Service"}],
        created_by_user_id=context["actor"].id,
    )
    test_db.add(config)
    test_db.commit()
    test_db.refresh(config)

    record = SanctionRecord(
        school_id=context["school"].id,
        event_id=context["event"].id,
        sanction_config_id=config.id,
        student_profile_id=context["student_profile"].id,
        assigned_by_user_id=context["actor"].id,
    )
    test_db.add(record)
    test_db.commit()

    duplicate = SanctionRecord(
        school_id=context["school"].id,
        event_id=context["event"].id,
        sanction_config_id=config.id,
        student_profile_id=context["student_profile"].id,
        assigned_by_user_id=context["actor"].id,
    )
    test_db.add(duplicate)

    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()


def test_sanction_item_is_unique_per_record_item_code(test_db):
    context = _seed_sanctions_context(test_db)

    config = EventSanctionConfig(
        school_id=context["school"].id,
        event_id=context["event"].id,
        sanctions_enabled=True,
        item_definitions_json=[{"code": "community_service", "name": "Community Service"}],
        created_by_user_id=context["actor"].id,
    )
    test_db.add(config)
    test_db.commit()
    test_db.refresh(config)

    record = SanctionRecord(
        school_id=context["school"].id,
        event_id=context["event"].id,
        sanction_config_id=config.id,
        student_profile_id=context["student_profile"].id,
        assigned_by_user_id=context["actor"].id,
    )
    test_db.add(record)
    test_db.commit()
    test_db.refresh(record)

    item = SanctionItem(
        sanction_record_id=record.id,
        item_code="community_service",
        item_name="Community Service",
    )
    test_db.add(item)
    test_db.commit()

    duplicate = SanctionItem(
        sanction_record_id=record.id,
        item_code="community_service",
        item_name="Community Service - Duplicate",
    )
    test_db.add(duplicate)

    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()


def test_sanction_delegation_is_unique_per_event_and_governance_unit(test_db):
    context = _seed_sanctions_context(test_db)

    config = EventSanctionConfig(
        school_id=context["school"].id,
        event_id=context["event"].id,
        sanctions_enabled=True,
        item_definitions_json=[{"code": "community_service", "name": "Community Service"}],
        created_by_user_id=context["actor"].id,
    )
    test_db.add(config)
    test_db.commit()
    test_db.refresh(config)

    delegation = SanctionDelegation(
        school_id=context["school"].id,
        event_id=context["event"].id,
        sanction_config_id=config.id,
        delegated_by_user_id=context["actor"].id,
        delegated_to_governance_unit_id=context["governance_unit"].id,
    )
    test_db.add(delegation)
    test_db.commit()

    duplicate = SanctionDelegation(
        school_id=context["school"].id,
        event_id=context["event"].id,
        sanction_config_id=config.id,
        delegated_by_user_id=context["actor"].id,
        delegated_to_governance_unit_id=context["governance_unit"].id,
    )
    test_db.add(duplicate)

    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()


def test_clearance_deadline_defaults_to_active_status(test_db):
    context = _seed_sanctions_context(test_db)

    deadline = ClearanceDeadline(
        school_id=context["school"].id,
        event_id=context["event"].id,
        declared_by_user_id=context["actor"].id,
        target_governance_unit_id=context["governance_unit"].id,
        deadline_at=datetime.utcnow() + timedelta(days=7),
        message="Submit sanction compliance before clearance cutoff.",
    )
    test_db.add(deadline)
    test_db.commit()
    test_db.refresh(deadline)

    assert deadline.status == ClearanceDeadlineStatus.ACTIVE

"""Tests for Phase 11: event target scope RBAC enforcement.

Covers:
- Campus Admin can create events with ALL, YEAR_LEVEL, DEPARTMENT, COURSE,
  DEPARTMENT_YEAR, COURSE_YEAR targets.
- SG Officer cannot target another department.
- SG Officer cannot use ALL scope.
- ORG Officer cannot target another course.
- ORG Officer cannot use ALL scope.
- Backend returns 403 for forbidden targeting.
- validate_event_targets_for_actor unit tests (pure service layer).
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone

from app.services.event_target_permissions import validate_event_targets_for_actor
from app.models.governance_hierarchy import GovernanceUnit, GovernanceUnitType
from app.models.event import EventTargetScope
from app.schemas.event import EventTargetCreate
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(roles=None, school_id=1):
    user = MagicMock()
    user.id = 1
    user.school_id = school_id
    _role_codes = roles or []
    user.roles = [MagicMock(role=MagicMock(code=c)) for c in _role_codes]
    return user


def _make_governance_unit(unit_type, department_id=None, program_id=None, school_id=1):
    unit = MagicMock(spec=GovernanceUnit)
    unit.id = 99
    unit.school_id = school_id
    unit.unit_type = unit_type
    unit.department_id = department_id
    unit.program_id = program_id
    return unit


def _target(scope_type, *, year_level=None, department_id=None, course_id=None):
    return EventTargetCreate(
        scope_type=scope_type,
        year_level=year_level,
        department_id=department_id,
        course_id=course_id,
    )


# ---------------------------------------------------------------------------
# Unit tests: validate_event_targets_for_actor (service layer, no DB)
# ---------------------------------------------------------------------------

class TestValidateEventTargetsForActor:
    """Pure unit tests — mock the DB and governance service."""

    def _run(self, targets, governance_units, roles=None):
        """Call the validator with mocked dependencies."""
        import app.services.event_target_permissions as mod

        user = _make_user(roles=roles or [])
        db = MagicMock()

        original_has_any_role = mod.has_any_role
        original_get_units = mod.governance_hierarchy_service.get_governance_units_with_permission

        try:
            mod.has_any_role = lambda u, r: any(role in r for role in (roles or []))
            mod.governance_hierarchy_service.get_governance_units_with_permission = (
                lambda *a, **kw: governance_units
            )
            validate_event_targets_for_actor(db, current_user=user, event_targets=targets)
        finally:
            mod.has_any_role = original_has_any_role
            mod.governance_hierarchy_service.get_governance_units_with_permission = original_get_units

    # --- Campus Admin is unrestricted ---

    def test_campus_admin_allows_all_scope(self):
        self._run(
            [_target(EventTargetScope.ALL)],
            governance_units=[],
            roles=["campus_admin"],
        )

    def test_campus_admin_allows_year_level(self):
        self._run(
            [_target(EventTargetScope.YEAR_LEVEL, year_level=2)],
            governance_units=[],
            roles=["campus_admin"],
        )

    def test_campus_admin_allows_department(self):
        self._run(
            [_target(EventTargetScope.DEPARTMENT, department_id=5)],
            governance_units=[],
            roles=["campus_admin"],
        )

    def test_campus_admin_allows_course(self):
        self._run(
            [_target(EventTargetScope.COURSE, course_id=7)],
            governance_units=[],
            roles=["campus_admin"],
        )

    def test_campus_admin_allows_department_year(self):
        self._run(
            [_target(EventTargetScope.DEPARTMENT_YEAR, department_id=5, year_level=3)],
            governance_units=[],
            roles=["campus_admin"],
        )

    def test_campus_admin_allows_course_year(self):
        self._run(
            [_target(EventTargetScope.COURSE_YEAR, course_id=7, year_level=1)],
            governance_units=[],
            roles=["campus_admin"],
        )

    # --- SSG: ALL and YEAR_LEVEL only ---

    def test_ssg_allows_all_scope(self):
        ssg_unit = _make_governance_unit(GovernanceUnitType.SSG)
        self._run([_target(EventTargetScope.ALL)], governance_units=[ssg_unit])

    def test_ssg_allows_year_level(self):
        ssg_unit = _make_governance_unit(GovernanceUnitType.SSG)
        self._run(
            [_target(EventTargetScope.YEAR_LEVEL, year_level=3)],
            governance_units=[ssg_unit],
        )

    def test_ssg_forbids_department(self):
        ssg_unit = _make_governance_unit(GovernanceUnitType.SSG)
        with pytest.raises(HTTPException) as exc_info:
            self._run(
                [_target(EventTargetScope.DEPARTMENT, department_id=5)],
                governance_units=[ssg_unit],
            )
        assert exc_info.value.status_code == 403

    def test_ssg_forbids_course(self):
        ssg_unit = _make_governance_unit(GovernanceUnitType.SSG)
        with pytest.raises(HTTPException) as exc_info:
            self._run(
                [_target(EventTargetScope.COURSE, course_id=7)],
                governance_units=[ssg_unit],
            )
        assert exc_info.value.status_code == 403

    # --- SG: own department only ---

    def test_sg_allows_own_department(self):
        sg_unit = _make_governance_unit(GovernanceUnitType.SG, department_id=10)
        self._run(
            [_target(EventTargetScope.DEPARTMENT, department_id=10)],
            governance_units=[sg_unit],
        )

    def test_sg_allows_own_department_year(self):
        sg_unit = _make_governance_unit(GovernanceUnitType.SG, department_id=10)
        self._run(
            [_target(EventTargetScope.DEPARTMENT_YEAR, department_id=10, year_level=2)],
            governance_units=[sg_unit],
        )

    def test_sg_forbids_other_department(self):
        sg_unit = _make_governance_unit(GovernanceUnitType.SG, department_id=10)
        with pytest.raises(HTTPException) as exc_info:
            self._run(
                [_target(EventTargetScope.DEPARTMENT, department_id=99)],
                governance_units=[sg_unit],
            )
        assert exc_info.value.status_code == 403

    def test_sg_forbids_all_scope(self):
        sg_unit = _make_governance_unit(GovernanceUnitType.SG, department_id=10)
        with pytest.raises(HTTPException) as exc_info:
            self._run(
                [_target(EventTargetScope.ALL)],
                governance_units=[sg_unit],
            )
        assert exc_info.value.status_code == 403

    def test_sg_forbids_year_level_scope(self):
        sg_unit = _make_governance_unit(GovernanceUnitType.SG, department_id=10)
        with pytest.raises(HTTPException) as exc_info:
            self._run(
                [_target(EventTargetScope.YEAR_LEVEL, year_level=1)],
                governance_units=[sg_unit],
            )
        assert exc_info.value.status_code == 403

    def test_sg_forbids_course_scope(self):
        sg_unit = _make_governance_unit(GovernanceUnitType.SG, department_id=10)
        with pytest.raises(HTTPException) as exc_info:
            self._run(
                [_target(EventTargetScope.COURSE, course_id=5)],
                governance_units=[sg_unit],
            )
        assert exc_info.value.status_code == 403

    # --- ORG: own course only ---

    def test_org_allows_own_course(self):
        org_unit = _make_governance_unit(GovernanceUnitType.ORG, department_id=10, program_id=20)
        self._run(
            [_target(EventTargetScope.COURSE, course_id=20)],
            governance_units=[org_unit],
        )

    def test_org_allows_own_course_year(self):
        org_unit = _make_governance_unit(GovernanceUnitType.ORG, department_id=10, program_id=20)
        self._run(
            [_target(EventTargetScope.COURSE_YEAR, course_id=20, year_level=3)],
            governance_units=[org_unit],
        )

    def test_org_forbids_other_course(self):
        org_unit = _make_governance_unit(GovernanceUnitType.ORG, department_id=10, program_id=20)
        with pytest.raises(HTTPException) as exc_info:
            self._run(
                [_target(EventTargetScope.COURSE, course_id=99)],
                governance_units=[org_unit],
            )
        assert exc_info.value.status_code == 403

    def test_org_forbids_all_scope(self):
        org_unit = _make_governance_unit(GovernanceUnitType.ORG, department_id=10, program_id=20)
        with pytest.raises(HTTPException) as exc_info:
            self._run(
                [_target(EventTargetScope.ALL)],
                governance_units=[org_unit],
            )
        assert exc_info.value.status_code == 403

    def test_org_forbids_department_scope(self):
        org_unit = _make_governance_unit(GovernanceUnitType.ORG, department_id=10, program_id=20)
        with pytest.raises(HTTPException) as exc_info:
            self._run(
                [_target(EventTargetScope.DEPARTMENT, department_id=10)],
                governance_units=[org_unit],
            )
        assert exc_info.value.status_code == 403

    def test_org_forbids_year_level_scope(self):
        org_unit = _make_governance_unit(GovernanceUnitType.ORG, department_id=10, program_id=20)
        with pytest.raises(HTTPException) as exc_info:
            self._run(
                [_target(EventTargetScope.YEAR_LEVEL, year_level=2)],
                governance_units=[org_unit],
            )
        assert exc_info.value.status_code == 403

    # --- Empty targets: no restriction applied ---

    def test_empty_targets_always_passes(self):
        sg_unit = _make_governance_unit(GovernanceUnitType.SG, department_id=10)
        # Empty list means backend defaults to ALL — no scope check needed here.
        self._run([], governance_units=[sg_unit])

    # --- No governance units: pass-through (outer guard already rejected) ---

    def test_no_governance_units_passes(self):
        self._run(
            [_target(EventTargetScope.ALL)],
            governance_units=[],
        )


# ---------------------------------------------------------------------------
# Integration tests: HTTP endpoint enforcement
# ---------------------------------------------------------------------------

def _future_event_payload(name="Target RBAC Test"):
    now = datetime.now(timezone.utc)
    return {
        "name": name,
        "start_datetime": (now + timedelta(hours=2)).isoformat(),
        "end_datetime": (now + timedelta(hours=4)).isoformat(),
        "location": "Test Hall",
    }


def test_campus_admin_can_create_all_scope_event(client, campus_admin_headers):
    payload = {
        **_future_event_payload("ALL Scope Event"),
        "event_targets": [{"scope_type": "ALL"}],
    }
    r = client.post("/api/events/", headers=campus_admin_headers, json=payload)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert any(t["scope_type"] == "ALL" for t in data.get("event_targets", []))


def test_campus_admin_can_create_year_level_event(client, campus_admin_headers):
    payload = {
        **_future_event_payload("Year Level Scope Event"),
        "event_targets": [{"scope_type": "YEAR_LEVEL", "year_level": 2}],
    }
    r = client.post("/api/events/", headers=campus_admin_headers, json=payload)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert any(t["scope_type"] == "YEAR_LEVEL" for t in data.get("event_targets", []))


def test_student_cannot_create_event(client, student_headers):
    payload = {
        **_future_event_payload("Student Attempt"),
        "event_targets": [{"scope_type": "ALL"}],
    }
    r = client.post("/api/events/", headers=student_headers, json=payload)
    assert r.status_code == 403


def test_unauthenticated_cannot_create_event(client):
    payload = {
        **_future_event_payload("Unauth Attempt"),
        "event_targets": [{"scope_type": "ALL"}],
    }
    r = client.post("/api/events/", json=payload)
    assert r.status_code == 401


def test_campus_admin_can_update_event_targets(client, campus_admin_headers):
    # Create first
    r = client.post("/api/events/", headers=campus_admin_headers, json=_future_event_payload("Update Target Test"))
    assert r.status_code in (200, 201), r.text
    event_id = r.json()["id"]

    # Update with YEAR_LEVEL target
    r2 = client.patch(
        f"/api/events/{event_id}",
        headers=campus_admin_headers,
        json={"event_targets": [{"scope_type": "YEAR_LEVEL", "year_level": 3}]},
    )
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert any(t["scope_type"] == "YEAR_LEVEL" for t in data.get("event_targets", []))

"""Event target scope permission enforcement.

Rules (enforced server-side; frontend may mirror for UX only):

Campus Admin / Admin
    Unrestricted — all six EventTargetScope values are allowed.

SSG member with MANAGE_EVENTS
    Allowed: ALL, YEAR_LEVEL
    Rationale: SSG is school-wide; it may address all students or a year cohort.

SG member with MANAGE_EVENTS  (unit has department_id, no program_id)
    Allowed: DEPARTMENT (own dept), DEPARTMENT_YEAR (own dept + any year)
    Forbidden: ALL, YEAR_LEVEL, COURSE, COURSE_YEAR, any other department

ORG member with MANAGE_EVENTS  (unit has department_id + program_id)
    Allowed: COURSE (own program), COURSE_YEAR (own program + any year)
    Forbidden: ALL, YEAR_LEVEL, DEPARTMENT, DEPARTMENT_YEAR, any other program

Multi-school boundary is always enforced by the existing school_id checks in
the event CRUD layer; this module only validates the target scope itself.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.event import EventTargetScope
from app.models.governance_hierarchy import GovernanceUnit, GovernanceUnitType, PermissionCode
from app.models.user import User as UserModel
from app.core.security import has_any_role
from app.services import governance_hierarchy_service


def _get_event_write_units(db: Session, current_user: UserModel) -> list[GovernanceUnit]:
    """Return governance units where the actor holds MANAGE_EVENTS."""
    return governance_hierarchy_service.get_governance_units_with_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.MANAGE_EVENTS,
    )


def validate_event_targets_for_actor(
    db: Session,
    *,
    current_user: UserModel,
    event_targets: list,
) -> None:
    """Raise HTTP 403 when the actor is not allowed to use the requested target scopes.

    Parameters
    ----------
    event_targets:
        List of EventTargetCreate-like objects (must have .scope_type and
        optional .year_level / .department_id / .course_id attributes).
    """
    # Campus Admin and platform Admin are unrestricted.
    if has_any_role(current_user, ["admin", "campus_admin"]):
        return

    # No targets means the backend will default to ALL — treat as ALL.
    if not event_targets:
        return

    governance_units = _get_event_write_units(db, current_user)

    # If the actor has no governance units with MANAGE_EVENTS, the outer
    # _ensure_event_manager guard already rejected the request.  We only
    # reach here when at least one unit exists.
    if not governance_units:
        return

    for target in event_targets:
        _validate_single_target(target, governance_units=governance_units)


def _validate_single_target(target, *, governance_units: list[GovernanceUnit]) -> None:
    """Validate one EventTargetCreate against the actor's governance units."""
    scope = target.scope_type
    if isinstance(scope, str):
        scope = EventTargetScope(scope)

    # Check whether ANY of the actor's units permits this target.
    for unit in governance_units:
        if _unit_permits_target(unit, scope=scope, target=target):
            return

    # Build a human-readable description of what was attempted.
    scope_label = scope.value if hasattr(scope, "value") else str(scope)
    raise HTTPException(
        status_code=403,
        detail=(
            f"Your governance role does not permit targeting scope '{scope_label}'. "
            "SG officers may only target their assigned department. "
            "ORG officers may only target their assigned course."
        ),
    )


def _unit_permits_target(
    unit: GovernanceUnit,
    *,
    scope: EventTargetScope,
    target,
) -> bool:
    """Return True when this governance unit allows the requested target."""
    unit_type = unit.unit_type
    if isinstance(unit_type, str):
        unit_type = GovernanceUnitType(unit_type)

    if unit_type == GovernanceUnitType.SSG:
        # SSG is school-wide: ALL and YEAR_LEVEL are permitted.
        return scope in {EventTargetScope.ALL, EventTargetScope.YEAR_LEVEL}

    if unit_type == GovernanceUnitType.SG:
        # SG is department-scoped.
        if scope == EventTargetScope.DEPARTMENT:
            return _target_dept_matches(target, unit)
        if scope == EventTargetScope.DEPARTMENT_YEAR:
            return _target_dept_matches(target, unit)
        return False

    if unit_type == GovernanceUnitType.ORG:
        # ORG is program-scoped.
        if scope == EventTargetScope.COURSE:
            return _target_course_matches(target, unit)
        if scope == EventTargetScope.COURSE_YEAR:
            return _target_course_matches(target, unit)
        return False

    return False


def _target_dept_matches(target, unit: GovernanceUnit) -> bool:
    """Return True when the target's department_id matches the unit's department."""
    if unit.department_id is None:
        return False
    target_dept_id = getattr(target, "department_id", None)
    if target_dept_id is None:
        return False
    return int(target_dept_id) == int(unit.department_id)


def _target_course_matches(target, unit: GovernanceUnit) -> bool:
    """Return True when the target's course_id matches the unit's program."""
    if unit.program_id is None:
        return False
    target_course_id = getattr(target, "course_id", None)
    if target_course_id is None:
        return False
    return int(target_course_id) == int(unit.program_id)

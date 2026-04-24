"""Use: Contains the main backend rules for sanctions management logic.
Where to use: Use this from routers, workers, or other services when sanctions logic is needed.
Role: Service layer. It keeps business logic out of the route files.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
import io
import logging

from fastapi import HTTPException
from openpyxl import Workbook
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.timezones import utc_now
from app.core.security import get_school_id_with_admin_fallback, has_any_role
from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event as EventModel
from app.models.governance_hierarchy import (
    GovernanceMember,
    GovernanceUnit,
    GovernanceUnitType,
)
from app.models.sanctions import (
    ClearanceDeadline,
    ClearanceDeadlineStatus,
    EventSanctionConfig,
    SanctionComplianceHistory,
    SanctionComplianceStatus,
    SanctionDelegation,
    SanctionDelegationScopeType,
    SanctionItem,
    SanctionItemStatus,
    SanctionRecord,
)
from app.models.user import StudentProfile, User
from app.schemas.sanctions import (
    ClearanceDeadlineCreateRequest,
    ClearanceDeadlineResponse,
    PaginatedSanctionRecordsResponse,
    SanctionConfigItemInput,
    SanctionConfigResponse,
    SanctionConfigUpsertRequest,
    SanctionDelegationResponse,
    SanctionDelegationUpsertRequest,
    SanctionDashboardEventSummary,
    SanctionItemResponse,
    SanctionRecordResponse,
    SanctionStudentDetailResponse,
    SanctionStudentSummary,
    SanctionsDashboardResponse,
)
from app.services import governance_hierarchy_service
from app.services.event_attendance_service import get_event_participant_student_ids

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _EventSanctionAccess:
    owner_level: GovernanceUnitType
    can_read: bool
    can_write: bool
    can_set_delegation: bool
    has_ssg_full_read: bool
    visible_units: list[GovernanceUnit] | None
    owner_ssg: bool
    owner_sg_units: list[GovernanceUnit]
    owner_org_units: list[GovernanceUnit]
    delegated_sg_units: list[GovernanceUnit]
    delegated_org_units: list[GovernanceUnit]


def _build_full_name(user: User) -> str:
    name_parts = [
        (user.first_name or "").strip(),
        (user.middle_name or "").strip(),
        (user.last_name or "").strip(),
    ]
    full_name = " ".join(part for part in name_parts if part)
    return full_name or user.email


def _resolve_academic_term(source_date: datetime | date | None) -> tuple[str, str]:
    if source_date is None:
        source_date = utc_now()
    if isinstance(source_date, datetime):
        resolved_date = source_date.date()
    else:
        resolved_date = source_date

    year = resolved_date.year
    month = resolved_date.month
    if month >= 6:
        school_year = f"{year}-{year + 1}"
    else:
        school_year = f"{year - 1}-{year}"

    if 8 <= month <= 12:
        semester = "1st"
    elif 1 <= month <= 5:
        semester = "2nd"
    else:
        semester = "summer"

    return school_year, semester


def _get_event_scope_ids(event: EventModel) -> tuple[set[int], set[int]]:
    department_ids = {department.id for department in event.departments}
    program_ids = {program.id for program in event.programs}
    return department_ids, program_ids


def _infer_event_owner_level(event: EventModel) -> GovernanceUnitType:
    department_ids, program_ids = _get_event_scope_ids(event)
    if program_ids:
        return GovernanceUnitType.ORG
    if department_ids:
        return GovernanceUnitType.SG
    return GovernanceUnitType.SSG


def _get_school_event_or_404(
    db: Session,
    *,
    school_id: int,
    event_id: int,
) -> EventModel:
    event = (
        db.query(EventModel)
        .options(
            joinedload(EventModel.departments),
            joinedload(EventModel.programs),
        )
        .filter(
            EventModel.school_id == school_id,
            EventModel.id == event_id,
        )
        .first()
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


def _get_active_governance_memberships(
    db: Session,
    *,
    school_id: int,
    user_id: int,
) -> list[GovernanceMember]:
    return (
        db.query(GovernanceMember)
        .options(joinedload(GovernanceMember.governance_unit))
        .join(GovernanceUnit, GovernanceMember.governance_unit_id == GovernanceUnit.id)
        .filter(
            GovernanceMember.user_id == user_id,
            GovernanceMember.is_active.is_(True),
            GovernanceUnit.school_id == school_id,
            GovernanceUnit.is_active.is_(True),
        )
        .all()
    )


def _group_membership_units_by_type(
    memberships: list[GovernanceMember],
) -> dict[GovernanceUnitType, list[GovernanceUnit]]:
    grouped: dict[GovernanceUnitType, list[GovernanceUnit]] = defaultdict(list)
    for membership in memberships:
        grouped[membership.governance_unit.unit_type].append(membership.governance_unit)
    return grouped


def _unit_matches_event_scope(governance_unit: GovernanceUnit, event: EventModel) -> bool:
    department_ids, program_ids = _get_event_scope_ids(event)
    return governance_hierarchy_service.governance_unit_matches_event_scope(
        governance_unit,
        department_ids=department_ids,
        program_ids=program_ids,
    )


def _record_matches_any_scope_unit(record: SanctionRecord, scope_units: list[GovernanceUnit]) -> bool:
    student_profile = record.student_profile
    if student_profile is None:
        return False
    return governance_hierarchy_service.governance_units_match_student_scope(
        scope_units,
        department_id=student_profile.department_id,
        program_id=student_profile.program_id,
    )


def _load_active_event_delegations(
    db: Session,
    *,
    school_id: int,
    event_id: int,
) -> list[SanctionDelegation]:
    return (
        db.query(SanctionDelegation)
        .options(joinedload(SanctionDelegation.delegated_to_governance_unit))
        .filter(
            SanctionDelegation.school_id == school_id,
            SanctionDelegation.event_id == event_id,
            SanctionDelegation.is_active.is_(True),
        )
        .all()
    )


def _dedupe_units(units: list[GovernanceUnit]) -> list[GovernanceUnit]:
    deduped: list[GovernanceUnit] = []
    seen_unit_ids: set[int] = set()
    for unit in units:
        if unit.id in seen_unit_ids:
            continue
        seen_unit_ids.add(unit.id)
        deduped.append(unit)
    return deduped


def _resolve_delegated_units_for_actor(
    *,
    delegations: list[SanctionDelegation],
    actor_units: list[GovernanceUnit],
    expected_unit_type: GovernanceUnitType,
) -> list[GovernanceUnit]:
    actor_unit_ids = {unit.id for unit in actor_units if unit.unit_type == expected_unit_type}
    delegated_units: list[GovernanceUnit] = []
    for delegation in delegations:
        delegated_unit = delegation.delegated_to_governance_unit
        if delegated_unit is None:
            continue
        if delegated_unit.id not in actor_unit_ids:
            continue
        if not delegated_unit.is_active:
            continue
        if delegated_unit.unit_type != expected_unit_type:
            continue
        delegated_units.append(delegated_unit)
    return _dedupe_units(delegated_units)


def _evaluate_event_access(
    db: Session,
    *,
    current_user: User,
    school_id: int,
    event: EventModel,
) -> _EventSanctionAccess:
    owner_level = _infer_event_owner_level(event)

    if has_any_role(current_user, ["admin", "campus_admin"]):
        return _EventSanctionAccess(
            owner_level=owner_level,
            can_read=True,
            can_write=True,
            can_set_delegation=(owner_level != GovernanceUnitType.ORG),
            has_ssg_full_read=True,
            visible_units=None,
            owner_ssg=(owner_level == GovernanceUnitType.SSG),
            owner_sg_units=[],
            owner_org_units=[],
            delegated_sg_units=[],
            delegated_org_units=[],
        )

    memberships = _get_active_governance_memberships(
        db,
        school_id=school_id,
        user_id=current_user.id,
    )
    units_by_type = _group_membership_units_by_type(memberships)
    actor_ssg_units = units_by_type.get(GovernanceUnitType.SSG, [])
    actor_sg_units = units_by_type.get(GovernanceUnitType.SG, [])
    actor_org_units = units_by_type.get(GovernanceUnitType.ORG, [])

    has_ssg_role = has_any_role(current_user, ["ssg"])
    has_sg_role = has_any_role(current_user, ["sg"])
    has_org_role = has_any_role(current_user, ["org"])

    owner_ssg = bool(has_ssg_role and actor_ssg_units and owner_level == GovernanceUnitType.SSG)
    owner_sg_units = []
    owner_org_units = []

    if has_sg_role and owner_level == GovernanceUnitType.SG:
        owner_sg_units = [
            unit
            for unit in actor_sg_units
            if _unit_matches_event_scope(unit, event)
        ]
    if has_org_role and owner_level == GovernanceUnitType.ORG:
        owner_org_units = [
            unit
            for unit in actor_org_units
            if _unit_matches_event_scope(unit, event)
        ]

    delegations = _load_active_event_delegations(
        db,
        school_id=school_id,
        event_id=event.id,
    )
    delegated_sg_units: list[GovernanceUnit] = []
    delegated_org_units: list[GovernanceUnit] = []
    if has_sg_role and owner_level == GovernanceUnitType.SSG:
        delegated_sg_units = _resolve_delegated_units_for_actor(
            delegations=delegations,
            actor_units=actor_sg_units,
            expected_unit_type=GovernanceUnitType.SG,
        )
    if has_org_role and owner_level == GovernanceUnitType.SG:
        delegated_org_units = _resolve_delegated_units_for_actor(
            delegations=delegations,
            actor_units=actor_org_units,
            expected_unit_type=GovernanceUnitType.ORG,
        )

    has_ssg_full_read = bool(has_ssg_role and actor_ssg_units)
    can_read = bool(
        has_ssg_full_read
        or owner_ssg
        or owner_sg_units
        or owner_org_units
        or delegated_sg_units
        or delegated_org_units
    )
    can_write = bool(
        owner_ssg
        or owner_sg_units
        or owner_org_units
        or delegated_sg_units
        or delegated_org_units
    )
    can_set_delegation = bool(owner_ssg or owner_sg_units)
    if owner_level == GovernanceUnitType.ORG:
        can_set_delegation = False

    visible_units: list[GovernanceUnit] | None = None
    if not has_ssg_full_read:
        visible_units = _dedupe_units(
            owner_sg_units + owner_org_units + delegated_sg_units + delegated_org_units
        )

    return _EventSanctionAccess(
        owner_level=owner_level,
        can_read=can_read,
        can_write=can_write,
        can_set_delegation=can_set_delegation,
        has_ssg_full_read=has_ssg_full_read,
        visible_units=visible_units,
        owner_ssg=owner_ssg,
        owner_sg_units=owner_sg_units,
        owner_org_units=owner_org_units,
        delegated_sg_units=delegated_sg_units,
        delegated_org_units=delegated_org_units,
    )


def _require_event_access(
    db: Session,
    *,
    current_user: User,
    school_id: int,
    event_id: int,
    write: bool = False,
) -> tuple[EventModel, _EventSanctionAccess]:
    event = _get_school_event_or_404(db, school_id=school_id, event_id=event_id)
    access = _evaluate_event_access(
        db,
        current_user=current_user,
        school_id=school_id,
        event=event,
    )
    if write and not access.can_write:
        raise HTTPException(status_code=403, detail="You do not have sanction write access for this event")
    if not write and not access.can_read:
        raise HTTPException(status_code=404, detail="Event not found")
    return event, access


def _normalize_config_items(items: list[SanctionConfigItemInput]) -> list[dict]:
    normalized_items: list[dict] = []
    seen_item_codes: set[str] = set()
    for item in items:
        item_name = (item.item_name or "").strip()
        if not item_name:
            continue
        item_code = (item.item_code or "").strip().lower() or None
        if item_code is not None:
            if item_code in seen_item_codes:
                raise HTTPException(status_code=400, detail=f"Duplicate sanction item_code: {item_code}")
            seen_item_codes.add(item_code)

        normalized_items.append(
            {
                "item_code": item_code,
                "item_name": item_name,
                "item_description": (item.item_description or "").strip() or None,
                "metadata_json": item.metadata_json or None,
            }
        )
    return normalized_items


def _build_config_response(
    *,
    event_id: int,
    config: EventSanctionConfig | None,
) -> SanctionConfigResponse:
    if config is None:
        return SanctionConfigResponse(
            event_id=event_id,
            sanctions_enabled=False,
            items=[],
        )

    item_rows = config.item_definitions_json if isinstance(config.item_definitions_json, list) else []
    items: list[SanctionConfigItemInput] = []
    for item_row in item_rows:
        if not isinstance(item_row, dict):
            continue
        item_name = (item_row.get("item_name") or "").strip()
        if not item_name:
            continue
        item_code = item_row.get("item_code")
        item_description = item_row.get("item_description")
        metadata_json = item_row.get("metadata_json")
        items.append(
            SanctionConfigItemInput(
                item_code=item_code,
                item_name=item_name,
                item_description=item_description,
                metadata_json=metadata_json if isinstance(metadata_json, dict) else None,
            )
        )

    return SanctionConfigResponse(
        event_id=event_id,
        sanctions_enabled=bool(config.sanctions_enabled),
        items=items,
        created_by_user_id=config.created_by_user_id,
        updated_by_user_id=config.updated_by_user_id,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def get_event_sanction_config(
    db: Session,
    *,
    current_user: User,
    event_id: int,
) -> SanctionConfigResponse:
    school_id = get_school_id_with_admin_fallback(db, current_user)
    _require_event_access(
        db,
        current_user=current_user,
        school_id=school_id,
        event_id=event_id,
    )
    config = (
        db.query(EventSanctionConfig)
        .filter(
            EventSanctionConfig.school_id == school_id,
            EventSanctionConfig.event_id == event_id,
        )
        .first()
    )
    return _build_config_response(event_id=event_id, config=config)


def upsert_event_sanction_config(
    db: Session,
    *,
    current_user: User,
    event_id: int,
    payload: SanctionConfigUpsertRequest,
) -> SanctionConfigResponse:
    school_id = get_school_id_with_admin_fallback(db, current_user)
    _require_event_access(
        db,
        current_user=current_user,
        school_id=school_id,
        event_id=event_id,
        write=True,
    )
    config = (
        db.query(EventSanctionConfig)
        .filter(
            EventSanctionConfig.school_id == school_id,
            EventSanctionConfig.event_id == event_id,
        )
        .first()
    )
    normalized_items = _normalize_config_items(payload.items)

    if config is None:
        config = EventSanctionConfig(
            school_id=school_id,
            event_id=event_id,
            sanctions_enabled=payload.sanctions_enabled,
            item_definitions_json=normalized_items,
            created_by_user_id=current_user.id,
            updated_by_user_id=current_user.id,
        )
        db.add(config)
    else:
        config.sanctions_enabled = payload.sanctions_enabled
        config.item_definitions_json = normalized_items
        config.updated_by_user_id = current_user.id

    db.commit()
    db.refresh(config)
    return _build_config_response(event_id=event_id, config=config)


def _build_sanction_student_summary(student_profile: StudentProfile) -> SanctionStudentSummary:
    user = student_profile.user
    return SanctionStudentSummary(
        user_id=user.id,
        student_profile_id=student_profile.id,
        student_id=student_profile.student_id,
        email=user.email,
        first_name=user.first_name,
        middle_name=user.middle_name,
        last_name=user.last_name,
        department_id=student_profile.department_id,
        department_name=getattr(student_profile.department, "name", None),
        program_id=student_profile.program_id,
        program_name=getattr(student_profile.program, "name", None),
        year_level=student_profile.year_level,
    )


def _build_sanction_record_response(record: SanctionRecord) -> SanctionRecordResponse:
    if record.student_profile is None or record.student_profile.user is None:
        raise HTTPException(status_code=500, detail="Sanction record has no student profile linkage")

    sorted_items = sorted(
        list(record.items),
        key=lambda item: ((item.item_name or "").lower(), item.id),
    )
    return SanctionRecordResponse(
        id=record.id,
        event_id=record.event_id,
        status=record.status,
        notes=record.notes,
        complied_at=record.complied_at,
        assigned_by_user_id=record.assigned_by_user_id,
        delegated_governance_unit_id=record.delegated_governance_unit_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
        student=_build_sanction_student_summary(record.student_profile),
        items=[SanctionItemResponse.model_validate(item) for item in sorted_items],
    )


def list_event_sanctioned_students(
    db: Session,
    *,
    current_user: User,
    event_id: int,
    skip: int = 0,
    limit: int = 50,
    status_filter: SanctionComplianceStatus | None = None,
) -> PaginatedSanctionRecordsResponse:
    school_id = get_school_id_with_admin_fallback(db, current_user)
    _event, access = _require_event_access(
        db,
        current_user=current_user,
        school_id=school_id,
        event_id=event_id,
    )

    query = (
        db.query(SanctionRecord)
        .options(
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.user),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.department),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.program),
            selectinload(SanctionRecord.items),
        )
        .filter(
            SanctionRecord.school_id == school_id,
            SanctionRecord.event_id == event_id,
        )
        .order_by(SanctionRecord.created_at.desc(), SanctionRecord.id.desc())
    )
    if status_filter is not None:
        query = query.filter(SanctionRecord.status == status_filter)

    records = query.all()
    if access.visible_units is not None:
        records = [
            record
            for record in records
            if _record_matches_any_scope_unit(record, access.visible_units)
        ]

    total = len(records)
    safe_skip = max(0, skip)
    safe_limit = max(1, min(limit, 250))
    sliced_records = records[safe_skip : safe_skip + safe_limit]

    return PaginatedSanctionRecordsResponse(
        total=total,
        skip=safe_skip,
        limit=safe_limit,
        items=[_build_sanction_record_response(record) for record in sliced_records],
    )


def _get_school_student_profile_or_404(
    db: Session,
    *,
    school_id: int,
    user_id: int,
) -> StudentProfile:
    student_profile = (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.user),
            joinedload(StudentProfile.department),
            joinedload(StudentProfile.program),
        )
        .join(User, StudentProfile.user_id == User.id)
        .filter(
            StudentProfile.school_id == school_id,
            User.id == user_id,
        )
        .first()
    )
    if student_profile is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_profile


def _enqueue_celery_task(task, *args: object, **kwargs: object) -> bool:
    try:
        task.apply_async(args=args, kwargs=kwargs, retry=False)
        return True
    except Exception:
        logger.warning(
            "Sanctions Celery dispatch failed for task %s.",
            getattr(task, "name", repr(task)),
            exc_info=True,
        )
        return False


def _dispatch_sanction_notification_email(
    *,
    recipient_email: str,
    first_name: str | None,
    event_name: str,
    sanction_item_names: list[str],
) -> bool:
    from app.workers.tasks import send_sanction_notification_email

    return _enqueue_celery_task(
        send_sanction_notification_email,
        recipient_email,
        first_name,
        event_name,
        sanction_item_names,
    )


def _dispatch_clearance_deadline_warning_email(
    *,
    recipient_email: str,
    first_name: str | None,
    event_name: str,
    deadline_at_iso: str,
    message: str | None,
) -> bool:
    from app.workers.tasks import send_clearance_deadline_warning_email

    return _enqueue_celery_task(
        send_clearance_deadline_warning_email,
        recipient_email,
        first_name,
        event_name,
        deadline_at_iso,
        message,
    )


def _dispatch_sanction_compliance_confirmation_email(
    *,
    recipient_email: str,
    first_name: str | None,
    event_name: str,
) -> bool:
    from app.workers.tasks import send_sanction_compliance_confirmation_email

    return _enqueue_celery_task(
        send_sanction_compliance_confirmation_email,
        recipient_email,
        first_name,
        event_name,
    )


def approve_student_sanction(
    db: Session,
    *,
    current_user: User,
    event_id: int,
    user_id: int,
) -> SanctionRecordResponse:
    school_id = get_school_id_with_admin_fallback(db, current_user)
    event, access = _require_event_access(
        db,
        current_user=current_user,
        school_id=school_id,
        event_id=event_id,
        write=True,
    )
    student_profile = _get_school_student_profile_or_404(
        db,
        school_id=school_id,
        user_id=user_id,
    )
    sanction_record = (
        db.query(SanctionRecord)
        .options(
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.user),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.department),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.program),
            selectinload(SanctionRecord.items),
        )
        .filter(
            SanctionRecord.school_id == school_id,
            SanctionRecord.event_id == event_id,
            SanctionRecord.student_profile_id == student_profile.id,
        )
        .first()
    )
    if sanction_record is None:
        raise HTTPException(status_code=404, detail="Sanction record not found")

    if access.visible_units is not None and not _record_matches_any_scope_unit(sanction_record, access.visible_units):
        raise HTTPException(status_code=404, detail="Sanction record not found")

    already_complied = sanction_record.status == SanctionComplianceStatus.COMPLIED
    complied_at = utc_now()
    sanction_record.status = SanctionComplianceStatus.COMPLIED
    sanction_record.complied_at = complied_at

    if not already_complied:
        for item in sanction_record.items:
            if item.status == SanctionItemStatus.COMPLIED:
                continue
            item.status = SanctionItemStatus.COMPLIED
            item.complied_at = complied_at

        school_year, semester = _resolve_academic_term(event.end_datetime)
        if sanction_record.items:
            for item in sanction_record.items:
                db.add(
                    SanctionComplianceHistory(
                        school_id=school_id,
                        event_id=event.id,
                        sanction_record_id=sanction_record.id,
                        sanction_item_id=item.id,
                        student_profile_id=student_profile.id,
                        complied_on=complied_at.date(),
                        school_year=school_year,
                        semester=semester,
                        complied_by_user_id=current_user.id,
                        notes="Sanction item marked complied.",
                    )
                )
        else:
            db.add(
                SanctionComplianceHistory(
                    school_id=school_id,
                    event_id=event.id,
                    sanction_record_id=sanction_record.id,
                    sanction_item_id=None,
                    student_profile_id=student_profile.id,
                    complied_on=complied_at.date(),
                    school_year=school_year,
                    semester=semester,
                    complied_by_user_id=current_user.id,
                    notes="Sanction marked complied.",
                )
            )

    db.commit()
    db.refresh(sanction_record)
    if not already_complied:
        _dispatch_sanction_compliance_confirmation_email(
            recipient_email=student_profile.user.email,
            first_name=student_profile.user.first_name,
            event_name=event.name,
        )
    return _build_sanction_record_response(sanction_record)


def _build_delegation_response(delegation: SanctionDelegation) -> SanctionDelegationResponse:
    delegated_unit = delegation.delegated_to_governance_unit
    return SanctionDelegationResponse(
        id=delegation.id,
        event_id=delegation.event_id,
        delegated_by_user_id=delegation.delegated_by_user_id,
        delegated_to_governance_unit_id=delegation.delegated_to_governance_unit_id,
        delegated_to_unit_code=getattr(delegated_unit, "unit_code", None),
        delegated_to_unit_name=getattr(delegated_unit, "unit_name", None),
        delegated_to_unit_type=getattr(delegated_unit, "unit_type", None),
        scope_type=delegation.scope_type,
        scope_json=delegation.scope_json,
        is_active=delegation.is_active,
        revoked_at=delegation.revoked_at,
        revoked_by_user_id=delegation.revoked_by_user_id,
        created_at=delegation.created_at,
        updated_at=delegation.updated_at,
    )


def get_event_delegation_config(
    db: Session,
    *,
    current_user: User,
    event_id: int,
) -> list[SanctionDelegationResponse]:
    school_id = get_school_id_with_admin_fallback(db, current_user)
    _require_event_access(
        db,
        current_user=current_user,
        school_id=school_id,
        event_id=event_id,
    )
    rows = (
        db.query(SanctionDelegation)
        .options(joinedload(SanctionDelegation.delegated_to_governance_unit))
        .filter(
            SanctionDelegation.school_id == school_id,
            SanctionDelegation.event_id == event_id,
            SanctionDelegation.is_active.is_(True),
        )
        .order_by(SanctionDelegation.created_at.asc(), SanctionDelegation.id.asc())
        .all()
    )
    return [_build_delegation_response(row) for row in rows]


def set_event_delegation_config(
    db: Session,
    *,
    current_user: User,
    event_id: int,
    payload: SanctionDelegationUpsertRequest,
) -> list[SanctionDelegationResponse]:
    school_id = get_school_id_with_admin_fallback(db, current_user)
    event, access = _require_event_access(
        db,
        current_user=current_user,
        school_id=school_id,
        event_id=event_id,
        write=True,
    )
    if not access.can_set_delegation:
        raise HTTPException(status_code=403, detail="Only the event owner governance level can set delegation")
    if access.owner_level == GovernanceUnitType.ORG:
        raise HTTPException(status_code=400, detail="ORG-owned events do not support further delegation")

    expected_target_type = (
        GovernanceUnitType.SG if access.owner_level == GovernanceUnitType.SSG else GovernanceUnitType.ORG
    )
    target_payloads = payload.delegations
    target_unit_ids = [row.delegated_to_governance_unit_id for row in target_payloads]
    if len(target_unit_ids) != len(set(target_unit_ids)):
        raise HTTPException(status_code=400, detail="Delegation contains duplicate governance units")

    unit_map: dict[int, GovernanceUnit] = {}
    if target_unit_ids:
        units = (
            db.query(GovernanceUnit)
            .filter(
                GovernanceUnit.school_id == school_id,
                GovernanceUnit.id.in_(target_unit_ids),
                GovernanceUnit.is_active.is_(True),
            )
            .all()
        )
        unit_map = {unit.id: unit for unit in units}
        if len(unit_map) != len(target_unit_ids):
            raise HTTPException(status_code=404, detail="One or more delegation governance units were not found")

    owner_sg_unit_ids = {unit.id for unit in access.owner_sg_units}
    for row in target_payloads:
        governance_unit = unit_map[row.delegated_to_governance_unit_id]
        if governance_unit.unit_type != expected_target_type:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid delegation target unit type {governance_unit.unit_type.value}. "
                    f"Expected {expected_target_type.value} for this event owner level."
                ),
            )

        if access.owner_level == GovernanceUnitType.SG:
            if governance_unit.parent_unit_id not in owner_sg_unit_ids:
                raise HTTPException(
                    status_code=403,
                    detail="SG can only delegate sanctions to ORG units under their own SG unit.",
                )

    config = (
        db.query(EventSanctionConfig)
        .filter(
            EventSanctionConfig.school_id == school_id,
            EventSanctionConfig.event_id == event_id,
        )
        .first()
    )
    sanction_config_id = config.id if config is not None else None

    existing_rows = (
        db.query(SanctionDelegation)
        .filter(
            SanctionDelegation.school_id == school_id,
            SanctionDelegation.event_id == event_id,
        )
        .all()
    )
    existing_by_unit_id = {row.delegated_to_governance_unit_id: row for row in existing_rows}
    target_unit_id_set = set(target_unit_ids)
    now = utc_now()

    for existing_row in existing_rows:
        if existing_row.delegated_to_governance_unit_id in target_unit_id_set:
            continue
        existing_row.is_active = False
        existing_row.revoked_at = now
        existing_row.revoked_by_user_id = current_user.id

    for row in target_payloads:
        existing_row = existing_by_unit_id.get(row.delegated_to_governance_unit_id)
        if existing_row is None:
            db.add(
                SanctionDelegation(
                    school_id=school_id,
                    event_id=event.id,
                    sanction_config_id=sanction_config_id,
                    delegated_by_user_id=current_user.id,
                    delegated_to_governance_unit_id=row.delegated_to_governance_unit_id,
                    scope_type=row.scope_type,
                    scope_json=row.scope_json,
                    is_active=bool(row.is_active),
                    revoked_at=None,
                    revoked_by_user_id=None,
                )
            )
            continue

        existing_row.sanction_config_id = sanction_config_id
        existing_row.delegated_by_user_id = current_user.id
        existing_row.scope_type = row.scope_type
        existing_row.scope_json = row.scope_json
        existing_row.is_active = bool(row.is_active)
        if existing_row.is_active:
            existing_row.revoked_at = None
            existing_row.revoked_by_user_id = None
        else:
            existing_row.revoked_at = now
            existing_row.revoked_by_user_id = current_user.id

    db.commit()
    return get_event_delegation_config(
        db,
        current_user=current_user,
        event_id=event_id,
    )


def _event_is_owned_for_dashboard(access: _EventSanctionAccess) -> bool:
    if access.owner_ssg:
        return True
    if access.owner_sg_units:
        return True
    if access.owner_org_units:
        return True
    return False


def get_governance_sanctions_dashboard(
    db: Session,
    *,
    current_user: User,
) -> SanctionsDashboardResponse:
    school_id = get_school_id_with_admin_fallback(db, current_user)
    if has_any_role(current_user, ["student"]):
        raise HTTPException(status_code=403, detail="Students cannot access the governance sanctions dashboard")

    events = (
        db.query(EventModel)
        .options(
            joinedload(EventModel.departments),
            joinedload(EventModel.programs),
        )
        .filter(EventModel.school_id == school_id)
        .order_by(EventModel.start_datetime.desc(), EventModel.id.desc())
        .all()
    )

    absent_count_rows = (
        db.query(
            AttendanceModel.event_id,
            func.count(AttendanceModel.id),
        )
        .filter(
            AttendanceModel.event_id.in_([event.id for event in events] or [0]),
            AttendanceModel.status == "absent",
        )
        .group_by(AttendanceModel.event_id)
        .all()
    )
    absent_count_map = {event_id: count for event_id, count in absent_count_rows}

    sanction_count_rows = (
        db.query(
            SanctionRecord.event_id,
            SanctionRecord.status,
            func.count(SanctionRecord.id),
        )
        .filter(
            SanctionRecord.school_id == school_id,
            SanctionRecord.event_id.in_([event.id for event in events] or [0]),
        )
        .group_by(SanctionRecord.event_id, SanctionRecord.status)
        .all()
    )
    pending_map: dict[int, int] = defaultdict(int)
    complied_map: dict[int, int] = defaultdict(int)
    for event_id, status_value, count in sanction_count_rows:
        if status_value == SanctionComplianceStatus.COMPLIED:
            complied_map[event_id] = int(count)
        else:
            pending_map[event_id] = int(count)

    dashboard_events: list[SanctionDashboardEventSummary] = []
    total_participants = 0
    total_absent = 0
    total_pending = 0
    total_complied = 0

    for event in events:
        access = _evaluate_event_access(
            db,
            current_user=current_user,
            school_id=school_id,
            event=event,
        )
        if not _event_is_owned_for_dashboard(access) and not has_any_role(current_user, ["admin", "campus_admin"]):
            continue

        participant_count = len(get_event_participant_student_ids(db, event))
        absent_count = int(absent_count_map.get(event.id, 0))
        pending_sanctions = int(pending_map.get(event.id, 0))
        complied_sanctions = int(complied_map.get(event.id, 0))
        absence_rate_percent = round((absent_count / participant_count) * 100, 2) if participant_count else 0.0

        total_participants += participant_count
        total_absent += absent_count
        total_pending += pending_sanctions
        total_complied += complied_sanctions

        dashboard_events.append(
            SanctionDashboardEventSummary(
                event_id=event.id,
                event_name=event.name,
                owner_level=access.owner_level,
                participant_count=participant_count,
                absent_count=absent_count,
                pending_sanctions=pending_sanctions,
                complied_sanctions=complied_sanctions,
                absence_rate_percent=absence_rate_percent,
            )
        )

    overall_absence_rate = round((total_absent / total_participants) * 100, 2) if total_participants else 0.0
    return SanctionsDashboardResponse(
        total_events=len(dashboard_events),
        total_participants=total_participants,
        total_absent=total_absent,
        total_pending_sanctions=total_pending,
        total_complied_sanctions=total_complied,
        overall_absence_rate_percent=overall_absence_rate,
        events=dashboard_events,
    )


def get_my_sanctions(
    db: Session,
    *,
    current_user: User,
) -> list[SanctionRecordResponse]:
    if not has_any_role(current_user, ["student"]):
        raise HTTPException(status_code=403, detail="Only students can access /students/me sanctions")
    school_id = get_school_id_with_admin_fallback(db, current_user)
    student_profile = _get_school_student_profile_or_404(
        db,
        school_id=school_id,
        user_id=current_user.id,
    )
    records = (
        db.query(SanctionRecord)
        .options(
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.user),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.department),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.program),
            selectinload(SanctionRecord.items),
        )
        .filter(
            SanctionRecord.school_id == school_id,
            SanctionRecord.student_profile_id == student_profile.id,
        )
        .order_by(SanctionRecord.created_at.desc(), SanctionRecord.id.desc())
        .all()
    )
    return [_build_sanction_record_response(record) for record in records]


def get_student_sanctions_detail(
    db: Session,
    *,
    current_user: User,
    user_id: int,
) -> SanctionStudentDetailResponse:
    school_id = get_school_id_with_admin_fallback(db, current_user)
    if has_any_role(current_user, ["student"]):
        raise HTTPException(status_code=403, detail="Students cannot access governance student sanctions detail")

    target_profile = _get_school_student_profile_or_404(
        db,
        school_id=school_id,
        user_id=user_id,
    )
    records = (
        db.query(SanctionRecord)
        .options(
            joinedload(SanctionRecord.event).joinedload(EventModel.departments),
            joinedload(SanctionRecord.event).joinedload(EventModel.programs),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.user),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.department),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.program),
            selectinload(SanctionRecord.items),
        )
        .filter(
            SanctionRecord.school_id == school_id,
            SanctionRecord.student_profile_id == target_profile.id,
        )
        .order_by(SanctionRecord.created_at.desc(), SanctionRecord.id.desc())
        .all()
    )

    access_by_event_id: dict[int, _EventSanctionAccess] = {}
    visible_records: list[SanctionRecordResponse] = []
    for record in records:
        event = record.event
        if event is None:
            continue
        access = access_by_event_id.get(event.id)
        if access is None:
            access = _evaluate_event_access(
                db,
                current_user=current_user,
                school_id=school_id,
                event=event,
            )
            access_by_event_id[event.id] = access

        if not access.can_read:
            continue
        if access.visible_units is not None and not _record_matches_any_scope_unit(record, access.visible_units):
            continue
        visible_records.append(_build_sanction_record_response(record))

    return SanctionStudentDetailResponse(
        user_id=user_id,
        sanctions=visible_records,
    )


def create_clearance_deadline(
    db: Session,
    *,
    current_user: User,
    payload: ClearanceDeadlineCreateRequest,
) -> ClearanceDeadlineResponse:
    school_id = get_school_id_with_admin_fallback(db, current_user)
    event, access = _require_event_access(
        db,
        current_user=current_user,
        school_id=school_id,
        event_id=payload.event_id,
        write=True,
    )

    if not has_any_role(current_user, ["ssg", "admin", "campus_admin"]):
        raise HTTPException(status_code=403, detail="Only SSG or admin users can declare sanctions clearance deadlines")
    if not has_any_role(current_user, ["admin", "campus_admin"]) and access.owner_level != GovernanceUnitType.SSG:
        raise HTTPException(status_code=403, detail="SSG may declare deadlines only on SSG-owned events")

    if payload.target_governance_unit_id is not None:
        target_unit = (
            db.query(GovernanceUnit)
            .filter(
                GovernanceUnit.school_id == school_id,
                GovernanceUnit.id == payload.target_governance_unit_id,
                GovernanceUnit.is_active.is_(True),
            )
            .first()
        )
        if target_unit is None:
            raise HTTPException(status_code=404, detail="Target governance unit not found")

    active_rows = (
        db.query(ClearanceDeadline)
        .filter(
            ClearanceDeadline.school_id == school_id,
            ClearanceDeadline.event_id == event.id,
            ClearanceDeadline.status == ClearanceDeadlineStatus.ACTIVE,
        )
        .all()
    )
    for row in active_rows:
        row.status = ClearanceDeadlineStatus.CLOSED

    deadline = ClearanceDeadline(
        school_id=school_id,
        event_id=event.id,
        declared_by_user_id=current_user.id,
        target_governance_unit_id=payload.target_governance_unit_id,
        deadline_at=payload.deadline_at,
        status=ClearanceDeadlineStatus.ACTIVE,
        message=(payload.message or "").strip() or None,
    )
    db.add(deadline)
    db.commit()
    db.refresh(deadline)

    pending_rows = (
        db.query(SanctionRecord)
        .options(joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.user))
        .filter(
            SanctionRecord.school_id == school_id,
            SanctionRecord.event_id == event.id,
            SanctionRecord.status == SanctionComplianceStatus.PENDING,
        )
        .all()
    )

    queued_emails = 0
    for row in pending_rows:
        student_profile = row.student_profile
        if student_profile is None or student_profile.user is None:
            continue
        queued = _dispatch_clearance_deadline_warning_email(
            recipient_email=student_profile.user.email,
            first_name=student_profile.user.first_name,
            event_name=event.name,
            deadline_at_iso=deadline.deadline_at.isoformat(),
            message=deadline.message,
        )
        if queued:
            queued_emails += 1

    now = utc_now()
    if queued_emails > 0:
        deadline.warning_email_sent_at = now
    deadline.warning_popup_sent_at = now
    db.commit()
    db.refresh(deadline)
    return ClearanceDeadlineResponse.model_validate(deadline)


def get_active_clearance_deadline(
    db: Session,
    *,
    current_user: User,
) -> ClearanceDeadlineResponse | None:
    school_id = get_school_id_with_admin_fallback(db, current_user)

    query = (
        db.query(ClearanceDeadline)
        .options(
            joinedload(ClearanceDeadline.event).joinedload(EventModel.departments),
            joinedload(ClearanceDeadline.event).joinedload(EventModel.programs),
        )
        .filter(
            ClearanceDeadline.school_id == school_id,
            ClearanceDeadline.status == ClearanceDeadlineStatus.ACTIVE,
        )
        .order_by(ClearanceDeadline.deadline_at.asc(), ClearanceDeadline.id.asc())
    )

    rows = query.all()
    if not rows:
        return None

    if has_any_role(current_user, ["student"]):
        student_profile = _get_school_student_profile_or_404(
            db,
            school_id=school_id,
            user_id=current_user.id,
        )
        pending_event_ids = {
            event_id
            for (event_id,) in (
                db.query(SanctionRecord.event_id)
                .filter(
                    SanctionRecord.school_id == school_id,
                    SanctionRecord.student_profile_id == student_profile.id,
                    SanctionRecord.status == SanctionComplianceStatus.PENDING,
                )
                .all()
            )
        }
        rows = [row for row in rows if row.event_id in pending_event_ids]
    else:
        filtered_rows: list[ClearanceDeadline] = []
        for row in rows:
            if row.event is None:
                continue
            access = _evaluate_event_access(
                db,
                current_user=current_user,
                school_id=school_id,
                event=row.event,
            )
            if access.can_read:
                filtered_rows.append(row)
        rows = filtered_rows

    if not rows:
        return None
    return ClearanceDeadlineResponse.model_validate(rows[0])


def _sanitize_sheet_title(raw_title: str, used_titles: set[str]) -> str:
    invalid_chars = {":", "\\", "/", "?", "*", "[", "]"}
    sanitized = "".join(ch for ch in raw_title if ch not in invalid_chars).strip() or "Sheet"
    sanitized = sanitized[:31]
    if sanitized not in used_titles:
        used_titles.add(sanitized)
        return sanitized

    suffix = 2
    while True:
        candidate = f"{sanitized[:28]}-{suffix}"[:31]
        if candidate not in used_titles:
            used_titles.add(candidate)
            return candidate
        suffix += 1


def export_event_sanctions_excel(
    db: Session,
    *,
    current_user: User,
    event_id: int,
) -> tuple[bytes, str]:
    school_id = get_school_id_with_admin_fallback(db, current_user)
    event, access = _require_event_access(
        db,
        current_user=current_user,
        school_id=school_id,
        event_id=event_id,
    )

    records = (
        db.query(SanctionRecord)
        .options(
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.user),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.department),
            joinedload(SanctionRecord.student_profile).joinedload(StudentProfile.program),
            selectinload(SanctionRecord.items),
        )
        .filter(
            SanctionRecord.school_id == school_id,
            SanctionRecord.event_id == event.id,
        )
        .order_by(SanctionRecord.id.asc())
        .all()
    )
    if access.visible_units is not None:
        records = [
            record
            for record in records
            if _record_matches_any_scope_unit(record, access.visible_units)
        ]

    workbook = Workbook()
    default_sheet = workbook.active
    workbook.remove(default_sheet)
    used_sheet_titles: set[str] = set()

    grouped_records: dict[str, list[SanctionRecord]] = defaultdict(list)
    for record in records:
        department_name = (
            getattr(record.student_profile.department, "name", None)
            if record.student_profile is not None
            else None
        ) or "Unassigned Department"
        grouped_records[department_name].append(record)

    if not grouped_records:
        grouped_records["Sanctions"] = []

    for department_name in sorted(grouped_records.keys(), key=lambda value: value.lower()):
        sheet_title = _sanitize_sheet_title(department_name, used_sheet_titles)
        sheet = workbook.create_sheet(title=sheet_title)
        sheet.append(
            [
                "Student ID",
                "Student Name",
                "Email",
                "Course",
                "Year Level",
                "Sanction Status",
                "Pending Items",
                "Complied Items",
                "Notes",
                "Complied At",
            ]
        )

        rows = grouped_records[department_name]
        rows.sort(
            key=lambda record: (
                (getattr(record.student_profile.program, "name", "") if record.student_profile else "").lower(),
                int(getattr(record.student_profile, "year_level", 0) or 0),
                (getattr(record.student_profile.user, "last_name", "") if record.student_profile else "").lower(),
                (getattr(record.student_profile.user, "first_name", "") if record.student_profile else "").lower(),
                record.id,
            )
        )
        for record in rows:
            student_profile = record.student_profile
            if student_profile is None or student_profile.user is None:
                continue
            user = student_profile.user
            pending_items = [item.item_name for item in record.items if item.status == SanctionItemStatus.PENDING]
            complied_items = [item.item_name for item in record.items if item.status == SanctionItemStatus.COMPLIED]
            sheet.append(
                [
                    student_profile.student_id or "",
                    _build_full_name(user),
                    user.email,
                    getattr(student_profile.program, "name", "") or "",
                    student_profile.year_level or "",
                    record.status.value,
                    ", ".join(pending_items),
                    ", ".join(complied_items),
                    record.notes or "",
                    record.complied_at.isoformat(sep=" ", timespec="minutes") if record.complied_at else "",
                ]
            )

    output = io.BytesIO()
    workbook.save(output)
    workbook.close()
    output.seek(0)

    filename = f"sanctions_event_{event.id}.xlsx"
    return output.read(), filename


def _extract_scope_ids(scope_json: dict | None, key: str) -> set[int]:
    if not isinstance(scope_json, dict):
        return set()
    raw_values = scope_json.get(key)
    if not isinstance(raw_values, list):
        return set()
    scope_ids: set[int] = set()
    for value in raw_values:
        try:
            scope_ids.add(int(value))
        except (TypeError, ValueError):
            continue
    return scope_ids


def _delegation_matches_student_scope(
    delegation: SanctionDelegation,
    student_profile: StudentProfile,
) -> bool:
    delegated_unit = delegation.delegated_to_governance_unit
    if delegated_unit is None:
        return False

    if delegation.scope_type == SanctionDelegationScopeType.SCHOOL:
        return True
    if delegation.scope_type == SanctionDelegationScopeType.UNIT:
        return governance_hierarchy_service.governance_units_match_student_scope(
            [delegated_unit],
            department_id=student_profile.department_id,
            program_id=student_profile.program_id,
        )
    if delegation.scope_type == SanctionDelegationScopeType.DEPARTMENT:
        department_scope = _extract_scope_ids(delegation.scope_json, "department_ids")
        if department_scope:
            return student_profile.department_id in department_scope
        if delegated_unit.department_id is not None:
            return student_profile.department_id == delegated_unit.department_id
        return False
    if delegation.scope_type == SanctionDelegationScopeType.PROGRAM:
        program_scope = _extract_scope_ids(delegation.scope_json, "program_ids")
        if program_scope:
            return student_profile.program_id in program_scope
        if delegated_unit.program_id is not None:
            return student_profile.program_id == delegated_unit.program_id
        return False
    return False


def _resolve_delegated_governance_unit_for_student(
    *,
    delegations: list[SanctionDelegation],
    student_profile: StudentProfile,
) -> int | None:
    for delegation in sorted(delegations, key=lambda row: (row.created_at, row.id)):
        if not delegation.is_active:
            continue
        if _delegation_matches_student_scope(delegation, student_profile):
            return delegation.delegated_to_governance_unit_id
    return None


def _normalize_item_definitions_for_generation(item_definitions_json: object) -> list[dict]:
    if not isinstance(item_definitions_json, list):
        return []
    normalized: list[dict] = []
    for raw_item in item_definitions_json:
        if not isinstance(raw_item, dict):
            continue
        item_name = (raw_item.get("item_name") or raw_item.get("name") or "").strip()
        if not item_name:
            continue
        item_code = (raw_item.get("item_code") or "").strip().lower() or None
        item_description = (raw_item.get("item_description") or raw_item.get("description") or "").strip() or None
        metadata_json = raw_item.get("metadata_json")
        normalized.append(
            {
                "item_code": item_code,
                "item_name": item_name,
                "item_description": item_description,
                "metadata_json": metadata_json if isinstance(metadata_json, dict) else None,
            }
        )
    return normalized


def generate_sanctions_for_completed_event(
    db: Session,
    event: EventModel,
) -> dict[str, int]:
    if db is None:
        return {
            "sanction_records_created": 0,
            "sanction_notification_emails_queued": 0,
        }
    if getattr(event, "id", None) is None or getattr(event, "school_id", None) is None:
        return {
            "sanction_records_created": 0,
            "sanction_notification_emails_queued": 0,
        }

    config = (
        db.query(EventSanctionConfig)
        .filter(
            EventSanctionConfig.school_id == event.school_id,
            EventSanctionConfig.event_id == event.id,
            EventSanctionConfig.sanctions_enabled.is_(True),
        )
        .first()
    )
    if config is None:
        return {
            "sanction_records_created": 0,
            "sanction_notification_emails_queued": 0,
        }

    absent_attendances = (
        db.query(AttendanceModel)
        .filter(
            AttendanceModel.event_id == event.id,
            AttendanceModel.status == "absent",
        )
        .all()
    )
    if not absent_attendances:
        return {
            "sanction_records_created": 0,
            "sanction_notification_emails_queued": 0,
        }

    absent_student_ids = {attendance.student_id for attendance in absent_attendances}
    student_profiles = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.user))
        .filter(
            StudentProfile.school_id == event.school_id,
            StudentProfile.id.in_(list(absent_student_ids)),
        )
        .all()
    )
    student_profile_map = {profile.id: profile for profile in student_profiles}

    existing_student_profile_ids = {
        student_profile_id
        for (student_profile_id,) in (
            db.query(SanctionRecord.student_profile_id)
            .filter(
                SanctionRecord.school_id == event.school_id,
                SanctionRecord.event_id == event.id,
            )
            .all()
        )
    }

    delegations = _load_active_event_delegations(
        db,
        school_id=event.school_id,
        event_id=event.id,
    )
    item_definitions = _normalize_item_definitions_for_generation(config.item_definitions_json)

    created_records = 0
    queued_notifications = 0
    for attendance in absent_attendances:
        student_profile = student_profile_map.get(attendance.student_id)
        if student_profile is None or student_profile.user is None:
            continue
        if student_profile.id in existing_student_profile_ids:
            continue

        delegated_governance_unit_id = _resolve_delegated_governance_unit_for_student(
            delegations=delegations,
            student_profile=student_profile,
        )

        sanction_record = SanctionRecord(
            school_id=event.school_id,
            event_id=event.id,
            sanction_config_id=config.id,
            student_profile_id=student_profile.id,
            attendance_id=attendance.id,
            delegated_governance_unit_id=delegated_governance_unit_id,
            status=SanctionComplianceStatus.PENDING,
            assigned_by_user_id=config.updated_by_user_id or config.created_by_user_id,
            notes="Auto-generated after event completion for absent attendance.",
        )
        db.add(sanction_record)
        db.flush()

        for item_definition in item_definitions:
            db.add(
                SanctionItem(
                    sanction_record_id=sanction_record.id,
                    item_code=item_definition["item_code"],
                    item_name=item_definition["item_name"],
                    item_description=item_definition["item_description"],
                    status=SanctionItemStatus.PENDING,
                    metadata_json=item_definition["metadata_json"],
                )
            )

        created_records += 1
        existing_student_profile_ids.add(student_profile.id)
        queued = _dispatch_sanction_notification_email(
            recipient_email=student_profile.user.email,
            first_name=student_profile.user.first_name,
            event_name=event.name,
            sanction_item_names=[item_definition["item_name"] for item_definition in item_definitions],
        )
        if queued:
            queued_notifications += 1

    return {
        "sanction_records_created": created_records,
        "sanction_notification_emails_queued": queued_notifications,
    }

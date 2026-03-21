"""Use: Handles event management and event timing actions API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs event management and event timing actions features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

from datetime import datetime, timedelta
import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_db
from app.core.event_defaults import resolve_governance_event_default_values
from app.core.security import get_current_user, get_school_id_or_403, has_any_role
from app.models.attendance import Attendance as AttendanceModel
from app.models.department import Department as DepartmentModel
from app.models.event import Event as EventModel, EventStatus as ModelEventStatus
from app.models.governance_hierarchy import GovernanceUnit, GovernanceUnitType, PermissionCode
from app.models.program import Program as ProgramModel
from app.models.school import SchoolSetting as SchoolSettingModel
from app.models.user import StudentProfile as StudentProfileModel, User as UserModel
from app.schemas.event import (
    Event as EventSchema,
    EventCreate,
    EventLocationVerificationRequest,
    EventLocationVerificationResponse,
    EventStatus,
    SignOutOverrideOpenRequest,
    EventTimeStatusInfo,
    EventUpdate,
    EventWithRelations,
)
from app.services import governance_hierarchy_service
from app.services.event_attendance_service import finalize_completed_event_attendance
from app.services.event_geolocation import (
    build_event_time_status_info,
    validate_event_geolocation_fields,
    verify_event_geolocation,
)
from app.services.event_time_status import get_event_timezone
from app.services.event_workflow_status import (
    sync_event_workflow_status,
    sync_scope_event_workflow_statuses,
)


router = APIRouter(prefix="/events", tags=["events"])
logger = logging.getLogger(__name__)


def _get_payload_fields_set(payload) -> set[str]:
    model_fields_set = getattr(payload, "model_fields_set", None)
    if model_fields_set is not None:
        return set(model_fields_set)
    return set(payload.__fields_set__)


def _ensure_event_manager(db: Session, current_user: UserModel) -> None:
    if has_any_role(current_user, ["admin", "campus_admin"]):
        return

    if governance_hierarchy_service.get_user_governance_unit_types(
        db,
        current_user=current_user,
    ):
        governance_hierarchy_service.ensure_governance_permission(
            db,
            current_user=current_user,
            permission_code=PermissionCode.MANAGE_EVENTS,
            detail=(
                "This governance account has no event features yet. "
                "Campus Admin must assign manage_events to the governance member."
            ),
        )
        return

    raise HTTPException(status_code=403, detail="Not authorized to manage events")


def _ensure_event_attendance_manager(db: Session, current_user: UserModel) -> None:
    if has_any_role(current_user, ["admin", "campus_admin"]):
        return

    if governance_hierarchy_service.get_user_governance_unit_types(
        db,
        current_user=current_user,
    ):
        governance_hierarchy_service.ensure_governance_permission(
            db,
            current_user=current_user,
            permission_code=PermissionCode.MANAGE_ATTENDANCE,
            detail=(
                "This governance account has no attendance features yet. "
                "Campus Admin must assign manage_attendance to the governance member."
            ),
        )
        return

    raise HTTPException(status_code=403, detail="Not authorized to manage event attendance")


def _actor_school_scope_id(current_user: UserModel) -> Optional[int]:
    if has_any_role(current_user, ["admin"]) and getattr(current_user, "school_id", None) is None:
        return None
    return get_school_id_or_403(current_user)


def _require_school_scope(current_user: UserModel) -> int:
    school_id = _actor_school_scope_id(current_user)
    if school_id is None:
        raise HTTPException(
            status_code=403,
            detail="Platform admin cannot perform school-scoped event writes without school context.",
        )
    return school_id


def _school_scoped_event_query(db: Session, school_id: Optional[int]):
    query = db.query(EventModel)
    if school_id is not None:
        query = query.filter(EventModel.school_id == school_id)
    return query


def _get_school_settings(db: Session, *, school_id: int) -> SchoolSettingModel | None:
    return (
        db.query(SchoolSettingModel)
        .filter(SchoolSettingModel.school_id == school_id)
        .first()
    )


def _persist_scope_status_sync(db: Session, school_id: Optional[int]) -> None:
    results = sync_scope_event_workflow_statuses(db, school_id=school_id)
    if any(result.changed for result in results):
        db.commit()


def _persist_event_status_sync(db: Session, event: EventModel) -> None:
    result = sync_event_workflow_status(db, event)
    if result.changed:
        db.commit()
        db.refresh(event)


def _get_event_scope_ids(event: EventModel) -> tuple[set[int], set[int]]:
    return (
        {department.id for department in event.departments},
        {program.id for program in event.programs},
    )


def _get_actor_student_profile(db: Session, current_user: UserModel) -> Optional[StudentProfileModel]:
    school_id = _actor_school_scope_id(current_user)
    if school_id is None:
        return None
    return (
        db.query(StudentProfileModel)
        .filter(
            StudentProfileModel.user_id == current_user.id,
            StudentProfileModel.school_id == school_id,
        )
        .first()
    )


def _event_is_visible_to_student_profile(
    event: EventModel,
    student_profile: Optional[StudentProfileModel],
) -> bool:
    if student_profile is None:
        return False

    event_department_ids, event_program_ids = _get_event_scope_ids(event)
    if not event_department_ids and not event_program_ids:
        return True
    if event_department_ids and student_profile.department_id not in event_department_ids:
        return False
    if event_program_ids and student_profile.program_id not in event_program_ids:
        return False
    return True


def _filter_events_to_student_scope(
    events: list[EventModel],
    *,
    student_profile: Optional[StudentProfileModel],
) -> list[EventModel]:
    if student_profile is None:
        return []
    return [event for event in events if _event_is_visible_to_student_profile(event, student_profile)]


def _filter_events_for_actor(
    db: Session,
    *,
    current_user: UserModel,
    governance_context: GovernanceUnitType | None,
    events: list[EventModel],
) -> list[EventModel]:
    filtered_events = _filter_events_to_governance_scope(
        events,
        _get_governance_event_units(
            db,
            current_user=current_user,
            governance_context=governance_context,
        ),
    )

    if governance_context is not None or has_any_role(current_user, ["admin", "campus_admin"]):
        return filtered_events

    return _filter_events_to_student_scope(
        filtered_events,
        student_profile=_get_actor_student_profile(db, current_user),
    )


def _get_governance_event_units(
    db: Session,
    *,
    current_user: UserModel,
    governance_context: GovernanceUnitType | None,
) -> list:
    if has_any_role(current_user, ["admin", "campus_admin"]):
        return []

    if governance_context is None:
        return []

    governance_units = governance_hierarchy_service.get_governance_units_with_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.MANAGE_EVENTS,
        unit_type=governance_context,
    )
    if governance_units:
        return governance_units

    governance_unit_types = governance_hierarchy_service.get_user_governance_unit_types(
        db,
        current_user=current_user,
    )
    if governance_context in governance_unit_types:
        raise HTTPException(
            status_code=403,
            detail=(
                "This governance account has no event features yet. "
                "The parent governance manager must assign manage_events first."
            ),
        )
    raise HTTPException(
        status_code=403,
        detail="You do not have access to this governance event scope.",
    )


def _get_governance_event_write_units(
    db: Session,
    *,
    current_user: UserModel,
    governance_context: GovernanceUnitType | None,
) -> list:
    if has_any_role(current_user, ["admin", "campus_admin"]):
        return []

    if governance_context is not None:
        return _get_governance_event_units(
            db,
            current_user=current_user,
            governance_context=governance_context,
        )

    return governance_hierarchy_service.get_governance_units_with_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.MANAGE_EVENTS,
    )


def _get_governance_attendance_units(
    db: Session,
    *,
    current_user: UserModel,
    governance_context: GovernanceUnitType | None,
) -> list:
    if has_any_role(current_user, ["admin", "campus_admin"]):
        return []

    governance_units = governance_hierarchy_service.get_governance_units_with_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.MANAGE_ATTENDANCE,
        unit_type=governance_context,
    )
    if governance_units:
        return governance_units

    if governance_context is not None:
        governance_unit_types = governance_hierarchy_service.get_user_governance_unit_types(
            db,
            current_user=current_user,
        )
        if governance_context in governance_unit_types:
            raise HTTPException(
                status_code=403,
                detail=(
                    "This governance account has no attendance features yet. "
                    "The parent governance manager must assign manage_attendance first."
                ),
            )

    if governance_context is not None:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this governance attendance scope.",
        )

    return governance_units


def _event_is_within_governance_units(event: EventModel, governance_units: list) -> bool:
    event_department_ids, event_program_ids = _get_event_scope_ids(event)
    return any(
        governance_hierarchy_service.governance_unit_matches_event_scope(
            governance_unit,
            department_ids=event_department_ids,
            program_ids=event_program_ids,
        )
        for governance_unit in governance_units
    )


def _filter_events_to_governance_scope(events: list[EventModel], governance_units: list) -> list[EventModel]:
    if not governance_units:
        return events
    return [event for event in events if _event_is_within_governance_units(event, governance_units)]


def _ensure_event_is_visible_in_governance_scope(
    db: Session,
    *,
    current_user: UserModel,
    event: EventModel,
    governance_context: GovernanceUnitType | None,
) -> None:
    governance_units = _get_governance_event_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    if governance_units and not _event_is_within_governance_units(event, governance_units):
        raise HTTPException(status_code=404, detail="Event not found")


def _ensure_event_is_writable_in_governance_scope(
    db: Session,
    *,
    current_user: UserModel,
    event: EventModel,
    governance_context: GovernanceUnitType | None,
) -> None:
    governance_units = _get_governance_event_write_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    if governance_units and not _event_is_within_governance_units(event, governance_units):
        raise HTTPException(status_code=404, detail="Event not found")


def _ensure_event_is_attendance_writable_in_governance_scope(
    db: Session,
    *,
    current_user: UserModel,
    event: EventModel,
    governance_context: GovernanceUnitType | None,
) -> None:
    governance_units = _get_governance_attendance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    if governance_units and not _event_is_within_governance_units(event, governance_units):
        raise HTTPException(status_code=404, detail="Event not found")


def _ensure_event_is_visible_for_actor(
    db: Session,
    *,
    current_user: UserModel,
    event: EventModel,
    governance_context: GovernanceUnitType | None,
) -> None:
    if governance_context is not None:
        _ensure_event_is_visible_in_governance_scope(
            db,
            current_user=current_user,
            event=event,
            governance_context=governance_context,
        )
        return

    if has_any_role(current_user, ["admin", "campus_admin"]):
        return

    if not _event_is_visible_to_student_profile(event, _get_actor_student_profile(db, current_user)):
        raise HTTPException(status_code=404, detail="Event not found")


def _resolve_governance_event_write_scope(
    db: Session,
    *,
    current_user: UserModel,
    governance_context: GovernanceUnitType | None,
) -> tuple[list[int], list[int]] | None:
    governance_unit, department_ids, program_ids = _resolve_governance_event_write_unit_and_scope(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    if governance_unit is None:
        return None
    return department_ids, program_ids


def _resolve_governance_event_write_unit_and_scope(
    db: Session,
    *,
    current_user: UserModel,
    governance_context: GovernanceUnitType | None,
) -> tuple[GovernanceUnit | None, list[int], list[int]]:
    governance_units = _get_governance_event_write_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    if not governance_units:
        return None, [], []

    if governance_context is None and len({unit.unit_type for unit in governance_units}) > 1:
        raise HTTPException(
            status_code=400,
            detail=(
                "This governance account manages multiple event scopes. "
                "Provide governance_context=SSG, SG, or ORG for event writes."
            ),
        )

    school_wide_units = [unit for unit in governance_units if unit.unit_type == GovernanceUnitType.SSG]
    if school_wide_units:
        return school_wide_units[0], [], []

    department_scopes = {
        unit.department_id
        for unit in governance_units
        if unit.unit_type == GovernanceUnitType.SG and unit.department_id is not None
    }
    if department_scopes:
        if len(department_scopes) != 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple SG event scopes were found for this account. Event writes need a single SG scope.",
            )
        department_id = next(iter(department_scopes))
        matching_unit = next(
            unit
            for unit in governance_units
            if unit.unit_type == GovernanceUnitType.SG and unit.department_id == department_id
        )
        return matching_unit, [department_id], []

    org_scopes = {
        (unit.department_id, unit.program_id)
        for unit in governance_units
        if unit.unit_type == GovernanceUnitType.ORG and unit.program_id is not None
    }
    if org_scopes:
        if len(org_scopes) != 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple ORG event scopes were found for this account. Event writes need a single ORG scope.",
            )
        department_id, program_id = next(iter(org_scopes))
        department_ids = [department_id] if department_id is not None else []
        matching_unit = next(
            unit
            for unit in governance_units
            if unit.unit_type == GovernanceUnitType.ORG
            and unit.department_id == department_id
            and unit.program_id == program_id
        )
        return matching_unit, department_ids, [program_id]

    return None, [], []


@router.post("/", response_model=EventWithRelations, status_code=status.HTTP_201_CREATED)
def create_event(
    event: EventCreate,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new event."""
    try:
        _ensure_event_manager(db, current_user)
        school_id = _require_school_scope(current_user)
        payload_fields_set = _get_payload_fields_set(event)

        if event.start_datetime >= event.end_datetime:
            raise HTTPException(status_code=400, detail="End datetime must be after start datetime")

        validate_event_geolocation_fields(
            latitude=event.geo_latitude,
            longitude=event.geo_longitude,
            radius_m=event.geo_radius_m,
            required=event.geo_required,
        )

        resolved_governance_unit, scoped_department_ids, scoped_program_ids = (
            _resolve_governance_event_write_unit_and_scope(
                db,
                current_user=current_user,
                governance_context=governance_context,
            )
        )
        school_settings = _get_school_settings(db, school_id=school_id)
        (
            default_early_check_in_minutes,
            default_late_threshold_minutes,
            default_sign_out_grace_minutes,
        ) = resolve_governance_event_default_values(
            school_settings=school_settings,
            governance_unit=resolved_governance_unit,
        )

        db_event = EventModel(
            school_id=school_id,
            name=event.name,
            location=event.location,
            geo_latitude=event.geo_latitude,
            geo_longitude=event.geo_longitude,
            geo_radius_m=event.geo_radius_m,
            geo_required=event.geo_required,
            geo_max_accuracy_m=event.geo_max_accuracy_m,
            early_check_in_minutes=(
                event.early_check_in_minutes
                if "early_check_in_minutes" in payload_fields_set
                else default_early_check_in_minutes
            ),
            late_threshold_minutes=(
                event.late_threshold_minutes
                if "late_threshold_minutes" in payload_fields_set
                else default_late_threshold_minutes
            ),
            sign_out_grace_minutes=(
                event.sign_out_grace_minutes
                if "sign_out_grace_minutes" in payload_fields_set
                else default_sign_out_grace_minutes
            ),
            sign_out_override_until=event.sign_out_override_until,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            status=ModelEventStatus[event.status.value.upper()],
        )
        db.add(db_event)
        db.flush()

        target_department_ids = list(event.department_ids or [])
        target_program_ids = list(event.program_ids or [])
        if resolved_governance_unit is not None:
            target_department_ids, target_program_ids = scoped_department_ids, scoped_program_ids

        if target_department_ids:
            departments = db.query(DepartmentModel).filter(
                DepartmentModel.school_id == school_id,
                DepartmentModel.id.in_(target_department_ids)
            ).all()
            if len(departments) != len(target_department_ids):
                missing = set(target_department_ids) - {department.id for department in departments}
                raise HTTPException(status_code=404, detail=f"Departments not found: {missing}")
            db_event.departments = departments

        if target_program_ids:
            programs = db.query(ProgramModel).options(
                joinedload(ProgramModel.departments)
            ).filter(
                ProgramModel.school_id == school_id,
                ProgramModel.id.in_(target_program_ids)
            ).all()
            if len(programs) != len(target_program_ids):
                missing = set(target_program_ids) - {program.id for program in programs}
                raise HTTPException(status_code=404, detail=f"Programs not found: {missing}")
            db_event.programs = programs

        auto_sync_result = None
        if db_event.status not in {ModelEventStatus.CANCELLED, ModelEventStatus.COMPLETED}:
            auto_sync_result = sync_event_workflow_status(db, db_event)

        if db_event.status == ModelEventStatus.COMPLETED and not (
            auto_sync_result and auto_sync_result.attendance_finalized
        ):
            finalize_completed_event_attendance(db, db_event)

        db.commit()
        db.refresh(db_event)
        return db_event

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Event creation failed (possible duplicate)")
    except Exception as exc:
        db.rollback()
        logger.error("Event creation error: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/", response_model=list[EventSchema])
def read_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[EventStatus] = None,
    start_from: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get paginated list of events with optional filters."""
    school_id = _actor_school_scope_id(current_user)
    _persist_scope_status_sync(db, school_id)

    query = _school_scoped_event_query(db, school_id).options(
        joinedload(EventModel.departments),
        joinedload(EventModel.programs),
    )
    if status:
        query = query.filter(EventModel.status == ModelEventStatus[status.value.upper()])
    if start_from:
        query = query.filter(EventModel.start_datetime >= start_from)
    if end_at:
        query = query.filter(EventModel.end_datetime <= end_at)

    events = query.order_by(EventModel.start_datetime).all()
    events = _filter_events_for_actor(
        db,
        current_user=current_user,
        governance_context=governance_context,
        events=events,
    )
    return events[skip : skip + limit]


@router.get("/ongoing", response_model=list[EventSchema])
def get_ongoing_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get all ongoing events."""
    school_id = _actor_school_scope_id(current_user)
    _persist_scope_status_sync(db, school_id)
    events = (
        _school_scoped_event_query(db, school_id)
        .options(
            joinedload(EventModel.departments),
            joinedload(EventModel.programs),
        )
        .filter(EventModel.status == ModelEventStatus.ONGOING)
        .order_by(EventModel.start_datetime)
        .all()
    )
    events = _filter_events_for_actor(
        db,
        current_user=current_user,
        governance_context=governance_context,
        events=events,
    )
    return events[skip : skip + limit]


@router.get("/{event_id}", response_model=EventWithRelations)
def read_event(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get complete event details with all relationships."""
    school_id = _actor_school_scope_id(current_user)
    event = (
        _school_scoped_event_query(db, school_id)
        .options(
            joinedload(EventModel.programs).joinedload(ProgramModel.departments),
            joinedload(EventModel.departments),
        )
        .filter(EventModel.id == event_id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    _ensure_event_is_visible_for_actor(
        db,
        current_user=current_user,
        event=event,
        governance_context=governance_context,
    )
    _persist_event_status_sync(db, event)
    return event


@router.get("/{event_id}/time-status", response_model=EventTimeStatusInfo)
def read_event_time_status(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    event = (
        _school_scoped_event_query(db, _actor_school_scope_id(current_user))
        .filter(EventModel.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    _ensure_event_is_visible_for_actor(
        db,
        current_user=current_user,
        event=event,
        governance_context=governance_context,
    )
    _persist_event_status_sync(db, event)
    return build_event_time_status_info(event)


@router.post("/{event_id}/sign-out-override/open", response_model=EventSchema)
def open_sign_out_override(
    event_id: int,
    payload: SignOutOverrideOpenRequest = Body(...),
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _ensure_event_attendance_manager(db, current_user)
    school_id = _require_school_scope(current_user)

    event = (
        _school_scoped_event_query(db, school_id)
        .options(
            joinedload(EventModel.departments),
            joinedload(EventModel.programs),
        )
        .filter(EventModel.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    _ensure_event_is_attendance_writable_in_governance_scope(
        db,
        current_user=current_user,
        event=event,
        governance_context=governance_context,
    )

    sync_result = sync_event_workflow_status(db, event)
    if sync_result.changed:
        db.commit()
        db.refresh(event)

    if event.status == ModelEventStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="Cancelled events cannot open sign-out early.")
    if event.status == ModelEventStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Sign-out is already closed for this event.")

    now_local = datetime.now(get_event_timezone()).replace(tzinfo=None, microsecond=0)
    if now_local < event.start_datetime:
        raise HTTPException(
            status_code=409,
            detail="Sign-out override can only be opened after the event has started.",
        )

    event.sign_out_override_until = now_local + timedelta(minutes=payload.override_minutes)
    sync_event_workflow_status(db, event, current_time=now_local)
    db.commit()
    db.refresh(event)
    return event


@router.post("/{event_id}/verify-location", response_model=EventLocationVerificationResponse)
def verify_event_location(
    event_id: int,
    payload: EventLocationVerificationRequest,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    event = (
        _school_scoped_event_query(db, _actor_school_scope_id(current_user))
        .filter(EventModel.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    _ensure_event_is_visible_for_actor(
        db,
        current_user=current_user,
        event=event,
        governance_context=governance_context,
    )
    _persist_event_status_sync(db, event)
    return verify_event_geolocation(
        event,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_m=payload.accuracy_m,
    )


@router.patch("/{event_id}", response_model=EventSchema)
def update_event(
    event_id: int,
    event_update: EventUpdate,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update event details."""
    try:
        _ensure_event_manager(db, current_user)
        school_id = _require_school_scope(current_user)

        db_event = (
            _school_scoped_event_query(db, school_id)
            .options(
                joinedload(EventModel.departments),
                joinedload(EventModel.programs),
            )
            .filter(EventModel.id == event_id)
            .first()
        )
        if not db_event:
            raise HTTPException(status_code=404, detail="Event not found")
        _ensure_event_is_writable_in_governance_scope(
            db,
            current_user=current_user,
            event=db_event,
            governance_context=governance_context,
        )

        was_completed = db_event.status == ModelEventStatus.COMPLETED

        new_start = (
            event_update.start_datetime
            if event_update.start_datetime is not None
            else db_event.start_datetime
        )
        new_end = (
            event_update.end_datetime
            if event_update.end_datetime is not None
            else db_event.end_datetime
        )
        if new_start >= new_end:
            raise HTTPException(status_code=400, detail="End datetime must be after start datetime")

        new_geo_latitude = (
            event_update.geo_latitude if event_update.geo_latitude is not None else db_event.geo_latitude
        )
        new_geo_longitude = (
            event_update.geo_longitude if event_update.geo_longitude is not None else db_event.geo_longitude
        )
        new_geo_radius = (
            event_update.geo_radius_m if event_update.geo_radius_m is not None else db_event.geo_radius_m
        )
        new_geo_required = (
            event_update.geo_required if event_update.geo_required is not None else bool(db_event.geo_required)
        )
        validate_event_geolocation_fields(
            latitude=new_geo_latitude,
            longitude=new_geo_longitude,
            radius_m=new_geo_radius,
            required=new_geo_required,
        )

        if event_update.name is not None:
            db_event.name = event_update.name
        if event_update.location is not None:
            db_event.location = event_update.location
        if event_update.geo_latitude is not None:
            db_event.geo_latitude = event_update.geo_latitude
        if event_update.geo_longitude is not None:
            db_event.geo_longitude = event_update.geo_longitude
        if event_update.geo_radius_m is not None:
            db_event.geo_radius_m = event_update.geo_radius_m
        if event_update.geo_required is not None:
            db_event.geo_required = event_update.geo_required
        if event_update.geo_max_accuracy_m is not None:
            db_event.geo_max_accuracy_m = event_update.geo_max_accuracy_m
        if event_update.early_check_in_minutes is not None:
            db_event.early_check_in_minutes = event_update.early_check_in_minutes
        if event_update.late_threshold_minutes is not None:
            db_event.late_threshold_minutes = event_update.late_threshold_minutes
        if event_update.sign_out_grace_minutes is not None:
            db_event.sign_out_grace_minutes = event_update.sign_out_grace_minutes
        if event_update.sign_out_override_until is not None:
            db_event.sign_out_override_until = event_update.sign_out_override_until
        db_event.start_datetime = new_start
        db_event.end_datetime = new_end
        if event_update.status is not None:
            db_event.status = ModelEventStatus[event_update.status.value.upper()]

        resolved_scope = _resolve_governance_event_write_scope(
            db,
            current_user=current_user,
            governance_context=governance_context,
        )
        target_department_ids = (
            list(event_update.department_ids) if event_update.department_ids is not None else None
        )
        target_program_ids = (
            list(event_update.program_ids) if event_update.program_ids is not None else None
        )
        if resolved_scope is not None:
            target_department_ids, target_program_ids = resolved_scope

        if target_department_ids is not None:
            db_event.departments = []
            db.flush()
            departments = db.query(DepartmentModel).filter(
                DepartmentModel.school_id == school_id,
                DepartmentModel.id.in_(target_department_ids)
            ).all()
            if len(departments) != len(target_department_ids):
                missing = set(target_department_ids) - {department.id for department in departments}
                raise HTTPException(status_code=404, detail=f"Departments not found: {missing}")
            db_event.departments = departments

        if target_program_ids is not None:
            db_event.programs = []
            db.flush()
            programs = db.query(ProgramModel).options(
                joinedload(ProgramModel.departments)
            ).filter(
                ProgramModel.school_id == school_id,
                ProgramModel.id.in_(target_program_ids)
            ).all()
            if len(programs) != len(target_program_ids):
                missing = set(target_program_ids) - {program.id for program in programs}
                raise HTTPException(status_code=404, detail=f"Programs not found: {missing}")
            db_event.programs = programs

        auto_sync_result = None
        if db_event.status not in {ModelEventStatus.CANCELLED, ModelEventStatus.COMPLETED}:
            auto_sync_result = sync_event_workflow_status(db, db_event)

        if db_event.status == ModelEventStatus.COMPLETED and not was_completed and not (
            auto_sync_result and auto_sync_result.attendance_finalized
        ):
            finalize_completed_event_attendance(db, db_event)

        db.commit()
        db.refresh(db_event)
        return db_event

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        logger.error("Integrity error during event update: %s", exc)
        raise HTTPException(status_code=400, detail="Update failed due to data integrity issues") from exc
    except ValueError as exc:
        db.rollback()
        logger.error("Value error during event update: %s", exc)
        raise HTTPException(status_code=400, detail=f"Invalid data format: {exc}") from exc
    except Exception as exc:
        db.rollback()
        logger.error("Unexpected error during event update: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _ensure_event_manager(db, current_user)
    school_id = _require_school_scope(current_user)

    event = (
        _school_scoped_event_query(db, school_id)
        .options(
            joinedload(EventModel.attendances),
            joinedload(EventModel.departments),
            joinedload(EventModel.programs),
        )
        .filter(EventModel.id == event_id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    _ensure_event_is_writable_in_governance_scope(
        db,
        current_user=current_user,
        event=event,
        governance_context=governance_context,
    )

    event.departments = []
    event.programs = []
    for attendance in event.attendances:
        db.delete(attendance)

    db.delete(event)
    db.commit()


@router.get("/{event_id}/attendees")
def get_event_attendees(
    event_id: int,
    status: Optional[EventStatus] = None,
    skip: int = 0,
    limit: int = 100,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get attendees for a specific event."""
    event = (
        _school_scoped_event_query(db, _actor_school_scope_id(current_user))
        .filter(EventModel.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    _ensure_event_is_visible_in_governance_scope(
        db,
        current_user=current_user,
        event=event,
        governance_context=governance_context,
    )

    _persist_event_status_sync(db, event)
    query = db.query(AttendanceModel).filter(AttendanceModel.event_id == event_id)
    if status:
        query = query.filter(AttendanceModel.status == status)

    return query.order_by(
        AttendanceModel.status,
        AttendanceModel.time_in,
    ).offset(skip).limit(limit).all()


@router.get("/{event_id}/stats")
def get_event_stats(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get attendance statistics for an event."""
    event = (
        _school_scoped_event_query(db, _actor_school_scope_id(current_user))
        .filter(EventModel.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    _ensure_event_is_visible_in_governance_scope(
        db,
        current_user=current_user,
        event=event,
        governance_context=governance_context,
    )

    _persist_event_status_sync(db, event)
    total = db.query(func.count(AttendanceModel.id)).filter(
        AttendanceModel.event_id == event_id
    ).scalar()

    counts = db.query(
        AttendanceModel.status,
        func.count(AttendanceModel.id),
    ).filter(
        AttendanceModel.event_id == event_id
    ).group_by(
        AttendanceModel.status
    ).all()

    return {
        "total": total,
        "statuses": {
            status_name: {
                "count": count,
                "percentage": round((count / total) * 100, 2) if total else 0,
            }
            for status_name, count in counts
        },
    }


@router.patch("/{event_id}/status", response_model=EventSchema)
def update_event_status(
    event_id: int,
    status: EventStatus,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update event status only."""
    try:
        _ensure_event_manager(db, current_user)
        school_id = _require_school_scope(current_user)

        db_event = (
            _school_scoped_event_query(db, school_id)
            .options(
                joinedload(EventModel.departments),
                joinedload(EventModel.programs),
            )
            .filter(EventModel.id == event_id)
            .first()
        )
        if not db_event:
            raise HTTPException(status_code=404, detail="Event not found")
        _ensure_event_is_writable_in_governance_scope(
            db,
            current_user=current_user,
            event=db_event,
            governance_context=governance_context,
        )

        was_completed = db_event.status == ModelEventStatus.COMPLETED
        db_event.status = ModelEventStatus[status.value.upper()]

        auto_sync_result = None
        if db_event.status not in {ModelEventStatus.CANCELLED, ModelEventStatus.COMPLETED}:
            auto_sync_result = sync_event_workflow_status(db, db_event)

        if db_event.status == ModelEventStatus.COMPLETED and not was_completed and not (
            auto_sync_result and auto_sync_result.attendance_finalized
        ):
            finalize_completed_event_attendance(db, db_event)

        db.commit()
        db.refresh(db_event)
        return db_event

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Status update error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}") from exc

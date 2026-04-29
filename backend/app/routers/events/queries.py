"""Read/query routes for the event router package."""

from .shared import *  # noqa: F403
from app.schemas.base import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[EventSchema])
def read_events(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[EventStatus] = None,
    start_from: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """List events visible to the actor. Read-only; does not mutate DB."""
    school_id = _actor_school_scope_id(current_user)

    query = _school_scoped_event_query(db, school_id).options(
        joinedload(EventModel.departments),
        joinedload(EventModel.programs),
        joinedload(EventModel.event_type),
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

    total = len(events)
    skip = (page - 1) * limit
    page_items = events[skip : skip + limit]
    return PaginatedResponse.build(page_items, total=total, page=page, limit=limit)


@router.get("/ongoing", response_model=PaginatedResponse[EventSchema])
def get_ongoing_events(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """List only currently ongoing events. Read-only; does not mutate DB."""
    school_id = _actor_school_scope_id(current_user)
    events = (
        _school_scoped_event_query(db, school_id)
        .options(
            joinedload(EventModel.departments),
            joinedload(EventModel.programs),
            joinedload(EventModel.event_type),
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

    total = len(events)
    skip = (page - 1) * limit
    page_items = events[skip : skip + limit]
    return PaginatedResponse.build(page_items, total=total, page=page, limit=limit)


@router.get("/{event_id}", response_model=EventWithRelations)
def read_event(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Load one event, enforce visibility. Read-only; does not mutate DB."""
    school_id = _actor_school_scope_id(current_user)
    event = (
        _school_scoped_event_query(db, school_id)
        .options(
            joinedload(EventModel.programs).joinedload(ProgramModel.departments),
            joinedload(EventModel.departments),
            joinedload(EventModel.event_type),
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
    return event


@router.get("/{event_id}/time-status", response_model=EventTimeStatusInfo)
def read_event_time_status(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Return the computed attendance time window state for one event. Read-only."""
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
    return build_event_time_status_info(event)


@router.post("/{event_id}/verify-location", response_model=EventLocationVerificationResponse)
def verify_event_location(
    event_id: int,
    payload: EventLocationVerificationRequest,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Check whether a provided location is inside the event geofence."""
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
    return verify_event_geolocation(
        event,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_m=payload.accuracy_m,
    )

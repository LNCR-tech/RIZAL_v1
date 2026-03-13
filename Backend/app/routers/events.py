from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session,joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

from app.schemas.event import (
    Event as EventSchema,
    EventCreate,
    EventLocationVerificationRequest,
    EventLocationVerificationResponse,
    EventUpdate,
    EventWithRelations,
    EventStatus,
    EventTimeStatusInfo,
)
from app.models.event import Event as EventModel, EventStatus as ModelEventStatus
from app.models.department import Department as DepartmentModel
from app.models.program import Program as ProgramModel
from app.models.user import SSGProfile
from app.database import get_db
from app.core.security import get_current_user, get_school_id_or_403, has_any_role
# Add these imports at the top of your event router (app/api/endpoints/event.py)
from typing import Optional  # For Optional type hint
from app.models.user import User as UserModel  # For UserModel
from app.models.attendance import Attendance as AttendanceModel  # For AttendanceModel
from sqlalchemy import func  # For aggregate functions
from app.services.event_attendance_service import finalize_completed_event_attendance
from app.services.event_geolocation import (
    build_event_time_status_info,
    validate_event_geolocation_fields,
    verify_event_geolocation,
)
from app.services.event_workflow_status import (
    sync_event_workflow_status,
    sync_scope_event_workflow_statuses,
)


router = APIRouter(prefix="/events", tags=["events"])
logger = logging.getLogger(__name__)


def _ensure_event_manager(current_user: UserModel) -> None:
    if not has_any_role(current_user, ["ssg", "school_IT", "school-it", "school_it", "event-organizer", "event_organizer"]):
        raise HTTPException(status_code=403, detail="Not authorized to manage events")


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


def _persist_scope_status_sync(db: Session, school_id: Optional[int]) -> None:
    results = sync_scope_event_workflow_statuses(db, school_id=school_id)
    if any(result.changed for result in results):
        db.commit()


def _persist_event_status_sync(db: Session, event: EventModel) -> None:
    result = sync_event_workflow_status(db, event)
    if result.changed:
        db.commit()
        db.refresh(event)

# 1. Create Event
@router.post("/", response_model=EventWithRelations, status_code=status.HTTP_201_CREATED)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create a new event"""
    try:
        _ensure_event_manager(current_user)
        school_id = _require_school_scope(current_user)
        
        # Validate datetime
        if event.start_datetime >= event.end_datetime:
            raise HTTPException(status_code=400, detail="End datetime must be after start datetime")
        validate_event_geolocation_fields(
            latitude=event.geo_latitude,
            longitude=event.geo_longitude,
            radius_m=event.geo_radius_m,
            required=event.geo_required,
        )
        
        # Create event
        db_event = EventModel(
            school_id=school_id,
            name=event.name,
            location=event.location,
            geo_latitude=event.geo_latitude,
            geo_longitude=event.geo_longitude,
            geo_radius_m=event.geo_radius_m,
            geo_required=event.geo_required,
            geo_max_accuracy_m=event.geo_max_accuracy_m,
            late_threshold_minutes=event.late_threshold_minutes,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            status=ModelEventStatus[event.status.value.upper()]
        )
        db.add(db_event)
        db.flush()  # Get ID before adding relationships
        
        # Add relationships
        if event.department_ids:
            departments = db.query(DepartmentModel).filter(
                DepartmentModel.id.in_(event.department_ids)
            ).all()
            if len(departments) != len(event.department_ids):
                missing = set(event.department_ids) - {d.id for d in departments}
                raise HTTPException(404, f"Departments not found: {missing}")
            db_event.departments = departments
        
        if event.program_ids:
            programs = db.query(ProgramModel).options(
            joinedload(ProgramModel.departments)  # Add this
        ).filter(
            ProgramModel.id.in_(event.program_ids)
        ).all()
            if len(programs) != len(event.program_ids):
                missing = set(event.program_ids) - {p.id for p in programs}
                raise HTTPException(404, f"Programs not found: {missing}")
            db_event.programs = programs
        
        if event.ssg_member_ids:
            ssg_profiles = (
                db.query(SSGProfile)
                .join(UserModel, SSGProfile.user_id == UserModel.id)
                .options(joinedload(SSGProfile.user))
                .filter(
                    SSGProfile.user_id.in_(event.ssg_member_ids),
                    UserModel.school_id == school_id,
                )
                .all()
            )

            if len(ssg_profiles) != len(event.ssg_member_ids):
                missing = set(event.ssg_member_ids) - {s.user_id for s in ssg_profiles}
                raise HTTPException(404, f"SSG members not found in this school: {missing}")

            db_event.ssg_members = ssg_profiles

        auto_sync_result = None
        if db_event.status not in {ModelEventStatus.CANCELLED, ModelEventStatus.COMPLETED}:
            auto_sync_result = sync_event_workflow_status(db, db_event)

        if db_event.status == ModelEventStatus.COMPLETED and not (
            auto_sync_result and auto_sync_result.attendance_finalized
        ):
            finalize_completed_event_attendance(db, db_event)
        
        db.commit()
        db.refresh(db_event)  # This should load departments/programs/ssg_members thanks to lazy="joined"
         # Debug: Verify loaded relationships
        print(f"Departments: {[d.id for d in db_event.departments]}")
        return db_event
        
    except HTTPException as he:
        db.rollback()
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Event creation failed (possible duplicate)")
    except Exception as e:
        db.rollback()
        logger.error(f"Event creation error: {str(e)}")
        raise HTTPException(500, "Internal server error")

# 2. Get All Events
@router.get("/", response_model=list[EventSchema])
def read_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[EventStatus] = None,
    start_from: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get paginated list of events with optional filters"""
    school_id = _actor_school_scope_id(current_user)
    _persist_scope_status_sync(db, school_id)
    query = _school_scoped_event_query(db, school_id).options(
        joinedload(EventModel.ssg_members).joinedload(SSGProfile.user)  # ← ADD THIS
    )
    if status:
        query = query.filter(EventModel.status == ModelEventStatus[status.value.upper()])
    if start_from:
        query = query.filter(EventModel.start_datetime >= start_from)
    if end_at:
        query = query.filter(EventModel.end_datetime <= end_at)
    
    events = query.order_by(EventModel.start_datetime).offset(skip).limit(limit).all()
    return events

# Add this endpoint to your router
@router.get("/ongoing", response_model=list[EventSchema])
def get_ongoing_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get all ongoing events"""
    school_id = _actor_school_scope_id(current_user)
    _persist_scope_status_sync(db, school_id)
    events = _school_scoped_event_query(db, school_id).options(
        joinedload(EventModel.departments),
        joinedload(EventModel.programs),
        joinedload(EventModel.ssg_members).joinedload(SSGProfile.user)
    ).filter(
        EventModel.status == ModelEventStatus.ONGOING
    ).order_by(EventModel.start_datetime).offset(skip).limit(limit).all()
    
    return events

# 3. Get Single Event
@router.get("/{event_id}", response_model=EventWithRelations)
def read_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get complete event details with all relationships"""
    school_id = _actor_school_scope_id(current_user)
    event = _school_scoped_event_query(db, school_id).options(
        joinedload(EventModel.programs).joinedload(ProgramModel.departments),
        joinedload(EventModel.departments),
        joinedload(EventModel.ssg_members).joinedload(SSGProfile.user)  # ← ADD THIS
    ).filter(EventModel.id == event_id).first()
    
    if not event:
        raise HTTPException(404, "Event not found")

    _persist_event_status_sync(db, event)
    return event


@router.get("/{event_id}/time-status", response_model=EventTimeStatusInfo)
def read_event_time_status(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    school_id = _actor_school_scope_id(current_user)
    event = (
        _school_scoped_event_query(db, school_id)
        .filter(EventModel.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    _persist_event_status_sync(db, event)
    return build_event_time_status_info(event)


@router.post("/{event_id}/verify-location", response_model=EventLocationVerificationResponse)
def verify_event_location(
    event_id: int,
    payload: EventLocationVerificationRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    school_id = _actor_school_scope_id(current_user)
    event = (
        _school_scoped_event_query(db, school_id)
        .filter(EventModel.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    _persist_event_status_sync(db, event)
    return verify_event_geolocation(
        event,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_m=payload.accuracy_m,
    )

# 4. Update Event
@router.patch("/{event_id}", response_model=EventSchema)
def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update event details"""
    try:
        _ensure_event_manager(current_user)
        school_id = _require_school_scope(current_user)
        
        # Get the existing event
        db_event = (
            _school_scoped_event_query(db, school_id)
            .options(
                joinedload(EventModel.departments),
                joinedload(EventModel.programs),
                joinedload(EventModel.ssg_members),
            )
            .filter(EventModel.id == event_id)
            .first()
        )
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        was_completed = db_event.status == ModelEventStatus.COMPLETED

        # Prepare the new datetime values
        new_start = event_update.start_datetime if event_update.start_datetime is not None else db_event.start_datetime
        new_end = event_update.end_datetime if event_update.end_datetime is not None else db_event.end_datetime

        # Validate datetime
        if new_start >= new_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End datetime must be after start datetime"
            )

        new_geo_latitude = event_update.geo_latitude if event_update.geo_latitude is not None else db_event.geo_latitude
        new_geo_longitude = event_update.geo_longitude if event_update.geo_longitude is not None else db_event.geo_longitude
        new_geo_radius = event_update.geo_radius_m if event_update.geo_radius_m is not None else db_event.geo_radius_m
        new_geo_required = event_update.geo_required if event_update.geo_required is not None else bool(db_event.geo_required)
        validate_event_geolocation_fields(
            latitude=new_geo_latitude,
            longitude=new_geo_longitude,
            radius_m=new_geo_radius,
            required=new_geo_required,
        )

        # Update basic fields
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
        if event_update.late_threshold_minutes is not None:
            db_event.late_threshold_minutes = event_update.late_threshold_minutes
        db_event.start_datetime = new_start
        db_event.end_datetime = new_end
        if event_update.status is not None:
            db_event.status = ModelEventStatus[event_update.status.value.upper()]

        # Update relationships if provided
        if event_update.department_ids is not None:
            db_event.departments = []
            db.flush()
            departments = db.query(DepartmentModel).filter(
                DepartmentModel.id.in_(event_update.department_ids)
            ).all()
            if len(departments) != len(event_update.department_ids):
                missing = set(event_update.department_ids) - {d.id for d in departments}
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Departments not found: {missing}"
                )
            db_event.departments = departments
        
        if event_update.program_ids is not None:
            db_event.programs = []
            db.flush()
            programs = db.query(ProgramModel).options(
            joinedload(ProgramModel.departments)
            ).filter(
            ProgramModel.id.in_(event_update.program_ids)
            ).all()
    
            if len(programs) != len(event_update.program_ids):
                missing = set(event_update.program_ids) - {p.id for p in programs}
                raise HTTPException(404, f"Programs not found: {missing}")
    
            db_event.programs = programs
        if event_update.ssg_member_ids is not None:
            db_event.ssg_members = []
            db.flush()
            ssg_profiles = (
                db.query(SSGProfile)
                .join(UserModel, SSGProfile.user_id == UserModel.id)
                .options(joinedload(SSGProfile.user))
                .filter(
                    SSGProfile.user_id.in_(event_update.ssg_member_ids),
                    UserModel.school_id == school_id,
                )
                .all()
            )
    
            if len(ssg_profiles) != len(event_update.ssg_member_ids):
                missing = set(event_update.ssg_member_ids) - {s.user_id for s in ssg_profiles}
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,detail=f"SSG members not found: {missing}")
            db_event.ssg_members = ssg_profiles

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
        
    except HTTPException as he:
        db.rollback()
        raise he
    except IntegrityError as ie:
        db.rollback()
        logger.error(f"Integrity error during event update: {str(ie)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update failed due to data integrity issues"
        )
    except ValueError as ve:
        db.rollback()
        logger.error(f"Value error during event update: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data format: {str(ve)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during event update: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# 5. Delete Event
@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)  # Require authentication
):
    # 1. Check if user has school IT or event-organizer role
    if not has_any_role(current_user, ["school_IT", "school-it", "school_it", "event-organizer", "event_organizer"]):
        raise HTTPException(403, "School IT or event-organizer access required")
    school_id = _require_school_scope(current_user)

    # 2. Find the event
    event = _school_scoped_event_query(db, school_id).options(
        joinedload(EventModel.attendances),
        joinedload(EventModel.departments),
        joinedload(EventModel.programs),
        joinedload(EventModel.ssg_members)
    ).filter(EventModel.id == event_id).first()

    if not event:
        raise HTTPException(404, "Event not found")

    # 3. Clear relationships (prevent foreign key errors)
    event.departments = []
    event.programs = []
    event.ssg_members = []

    # 4. Delete attendances (if cascade isn't working)
    for attendance in event.attendances:
        db.delete(attendance)

    # 5. Delete the event
    db.delete(event)
    db.commit()


# 6. Get Event Attendees
@router.get("/{event_id}/attendees")
def get_event_attendees(
    event_id: int,
    status: Optional[EventStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get attendees for a specific event"""
    school_id = _actor_school_scope_id(current_user)
    event = (
        _school_scoped_event_query(db, school_id)
        .filter(EventModel.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(404, "Event not found")

    _persist_event_status_sync(db, event)
    query = db.query(AttendanceModel).filter(
        AttendanceModel.event_id == event_id
    )
    
    if status:
        query = query.filter(AttendanceModel.status == status)
    
    return query.order_by(
        AttendanceModel.status,
        AttendanceModel.time_in
    ).offset(skip).limit(limit).all()

# 7. Get Event Statistics
@router.get("/{event_id}/stats")
def get_event_stats(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get attendance statistics for an event"""
    school_id = _actor_school_scope_id(current_user)
    event = (
        _school_scoped_event_query(db, school_id)
        .filter(EventModel.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(404, "Event not found")

    _persist_event_status_sync(db, event)
    total = db.query(func.count(AttendanceModel.id)).filter(
        AttendanceModel.event_id == event_id
    ).scalar()
    
    counts = db.query(
        AttendanceModel.status,
        func.count(AttendanceModel.id)
    ).filter(
        AttendanceModel.event_id == event_id
    ).group_by(
        AttendanceModel.status
    ).all()
    
    return {
        "total": total,
        "statuses": {
            status: {
                "count": count,
                "percentage": round((count / total) * 100, 2) if total else 0
            } for status, count in counts
        }
    }

# New endpoint to handle status updates only - add this to your router

@router.patch("/{event_id}/status", response_model=EventSchema)
def update_event_status(
    event_id: int,
    status: EventStatus,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update event status only"""
    try:
        _ensure_event_manager(current_user)
        school_id = _require_school_scope(current_user)
        
        # Get the existing event
        db_event = (
            _school_scoped_event_query(db, school_id)
            .options(
                joinedload(EventModel.departments),
                joinedload(EventModel.programs),
                joinedload(EventModel.ssg_members),
            )
            .filter(EventModel.id == event_id)
            .first()
        )
        if not db_event:
            raise HTTPException(404, "Event not found")
        was_completed = db_event.status == ModelEventStatus.COMPLETED
        
        # Update only the status
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
    except Exception as e:
        db.rollback()
        logger.error(f"Status update error: {str(e)}")
        raise HTTPException(500, f"Internal server error: {str(e)}")    

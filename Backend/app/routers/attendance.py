"""Use: Handles attendance check-in, check-out, and reports API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs attendance check-in, check-out, and reports features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, and_, or_, text, String
from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any

from app.models.user import User as UserModel
from app.models.attendance import Attendance as AttendanceModel
from app.models.user import StudentProfile
from app.schemas.attendance import AttendanceStatus, Attendance, AttendanceWithStudent, StudentAttendanceRecord, StudentAttendanceResponse, AttendanceReportResponse, StudentAttendanceSummary, StudentAttendanceDetail, StudentAttendanceReport, StudentListItem
from app.schemas.attendance_requests import BulkAttendanceRequest, ManualAttendanceRequest
from app.core.dependencies import get_db
from app.core.security import get_current_user, get_school_id_or_403, has_any_role
from app.models.user import User
from app.models.event import Event, EventStatus
from app.models.governance_hierarchy import GovernanceUnitType, PermissionCode
from app.models.program import Program
from app.services.attendance_status import (
    ATTENDED_STATUS_VALUES,
    empty_attendance_status_counts,
    finalize_completed_attendance_status,
    is_attended_status,
    normalize_attendance_status,
)
from app.services.event_time_status import get_attendance_decision, get_sign_out_decision
from app.services.event_workflow_status import sync_event_workflow_status
from app.services import governance_hierarchy_service


router = APIRouter(prefix="/attendance", tags=["attendance"])
logger = logging.getLogger(__name__)


def _get_attendance_governance_units(
    db: Session,
    *,
    current_user: UserModel,
    governance_context: GovernanceUnitType | None,
):
    if has_any_role(current_user, ["admin", "campus_admin"]):
        return []

    return governance_hierarchy_service.get_governance_units_with_permission(
        db,
        current_user=current_user,
        permission_code=PermissionCode.MANAGE_ATTENDANCE,
        unit_type=governance_context,
    )


def _apply_student_scope_filters(query, governance_units):
    if not governance_units:
        return query
    if any(unit.department_id is None and unit.program_id is None for unit in governance_units):
        return query

    filters = []
    for governance_unit in governance_units:
        condition_parts = []
        if governance_unit.department_id is not None:
            condition_parts.append(StudentProfile.department_id == governance_unit.department_id)
        if governance_unit.program_id is not None:
            condition_parts.append(StudentProfile.program_id == governance_unit.program_id)
        if condition_parts:
            filters.append(and_(*condition_parts))

    if not filters:
        return query.filter(text("1=0"))
    return query.filter(or_(*filters))


def _event_matches_governance_units(event: Event, governance_units) -> bool:
    if not governance_units:
        return True

    department_ids = {department.id for department in event.departments}
    program_ids = {program.id for program in event.programs}
    return any(
        governance_hierarchy_service.governance_unit_matches_event_scope(
            governance_unit,
            department_ids=department_ids,
            program_ids=program_ids,
        )
        for governance_unit in governance_units
    )


def _ensure_event_in_attendance_scope(event: Event, governance_units) -> None:
    if governance_units and not _event_matches_governance_units(event, governance_units):
        raise HTTPException(404, "Event not found")


def _ensure_student_in_attendance_scope(student: StudentProfile, governance_units) -> None:
    if governance_units and not governance_hierarchy_service.governance_units_match_student_scope(
        governance_units,
        department_id=student.department_id,
        program_id=student.program_id,
    ):
        raise HTTPException(404, "Student not found")


def _ensure_student_is_event_participant(student: StudentProfile, event: Event) -> None:
    event_program_ids = {program.id for program in event.programs}
    event_department_ids = {department.id for department in event.departments}
    if event_program_ids and student.program_id not in event_program_ids:
        raise HTTPException(400, "Student is outside the event program scope")
    if event_department_ids and student.department_id not in event_department_ids:
        raise HTTPException(400, "Student is outside the event department scope")


def _get_event_ids_in_attendance_scope(db: Session, *, school_id: int, governance_units) -> list[int]:
    if not governance_units:
        return [
            event_id
            for (event_id,) in db.query(Event.id).filter(Event.school_id == school_id).all()
        ]

    events = (
        db.query(Event)
        .options(
            joinedload(Event.departments),
            joinedload(Event.programs),
        )
        .filter(Event.school_id == school_id)
        .all()
    )
    return [event.id for event in events if _event_matches_governance_units(event, governance_units)]


def _get_event_in_school_or_404(db: Session, event_id: int, school_id: int) -> Event:
    event = db.query(Event).filter(Event.id == event_id, Event.school_id == school_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    result = sync_event_workflow_status(db, event)
    if result.changed:
        db.commit()
        db.refresh(event)
    return event


def _get_event_attendance_decision(event: Event) -> dict[str, Any]:
    decision = get_attendance_decision(
        start_time=event.start_datetime,
        end_time=event.end_datetime,
        early_check_in_minutes=getattr(event, "early_check_in_minutes", 0),
        late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
        sign_out_grace_minutes=getattr(event, "sign_out_grace_minutes", 0),
        sign_out_override_until=getattr(event, "sign_out_override_until", None),
        present_until_override_at=getattr(event, "present_until_override_at", None),
        late_until_override_at=getattr(event, "late_until_override_at", None),
    )
    return _serialize_attendance_decision(decision)


def _get_event_sign_out_decision(event: Event) -> dict[str, Any]:
    decision = get_sign_out_decision(
        start_time=event.start_datetime,
        end_time=event.end_datetime,
        early_check_in_minutes=getattr(event, "early_check_in_minutes", 0),
        late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
        sign_out_grace_minutes=getattr(event, "sign_out_grace_minutes", 0),
        sign_out_override_until=getattr(event, "sign_out_override_until", None),
        present_until_override_at=getattr(event, "present_until_override_at", None),
        late_until_override_at=getattr(event, "late_until_override_at", None),
    )
    return _serialize_attendance_decision(decision)


def _serialize_attendance_decision(decision) -> dict[str, Any]:
    payload = decision.to_dict()
    for key, value in list(payload.items()):
        if isinstance(value, datetime):
            payload[key] = value.isoformat()
    return payload


def _active_attendance_for_student_event(
    db: Session,
    *,
    student_profile_id: int,
    event_id: int,
) -> AttendanceModel | None:
    return (
        db.query(AttendanceModel)
        .filter(
            AttendanceModel.student_id == student_profile_id,
            AttendanceModel.event_id == event_id,
            AttendanceModel.time_out.is_(None),
        )
        .order_by(AttendanceModel.time_in.desc(), AttendanceModel.id.desc())
        .first()
    )


def _complete_attendance_sign_out(
    attendance: AttendanceModel,
    *,
    recorded_at: datetime,
) -> int:
    attendance.time_out = recorded_at
    attendance.check_out_status = "present"
    attendance.status, final_note = finalize_completed_attendance_status(
        check_in_status=attendance.check_in_status or attendance.status,
        check_out_status=attendance.check_out_status,
    )
    attendance.notes = final_note
    duration_seconds = (attendance.time_out - attendance.time_in).total_seconds()
    return int(max(0, duration_seconds / 60))

def _ensure_attendance_management_access(db: Session, current_user: UserModel) -> None:
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

    raise HTTPException(403, "Insufficient permissions")


def _ensure_event_report_access(db: Session, current_user: UserModel) -> None:
    _ensure_attendance_management_access(db, current_user)


def _ensure_attendance_report_access(db: Session, current_user: UserModel) -> None:
    _ensure_attendance_management_access(db, current_user)


def _ensure_attendance_operator_access(db: Session, current_user: UserModel) -> None:
    _ensure_attendance_management_access(db, current_user)


@router.get("/events/{event_id}/report", response_model=AttendanceReportResponse)
def get_event_attendance_report(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_event_report_access(db, current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    actor_school_id = None
    if not (has_any_role(current_user, ["admin"]) and getattr(current_user, "school_id", None) is None):
        actor_school_id = get_school_id_or_403(current_user)

    event_query = (
        db.query(Event)
        .options(
            joinedload(Event.programs),
            joinedload(Event.departments),
        )
        .filter(Event.id == event_id)
    )
    if actor_school_id is not None:
        event_query = event_query.filter(Event.school_id == actor_school_id)
    event = event_query.first()

    if not event:
        raise HTTPException(404, "Event not found")
    _ensure_event_in_attendance_scope(event, governance_units)
    sync_result = sync_event_workflow_status(db, event)
    if sync_result.changed:
        db.commit()
        db.refresh(event)
    school_id = event.school_id
    if school_id is None:
        raise HTTPException(400, "Event is not linked to a school")

    program_ids = [program.id for program in event.programs]
    department_ids = [department.id for department in event.departments]

    participant_query = (
        db.query(
            StudentProfile.id.label("student_id"),
            StudentProfile.program_id.label("program_id"),
        )
        .join(User, StudentProfile.user_id == User.id)
        .filter(User.school_id == school_id)
    )

    if program_ids:
        participant_query = participant_query.filter(StudentProfile.program_id.in_(program_ids))
    if department_ids:
        participant_query = participant_query.filter(StudentProfile.department_id.in_(department_ids))

    participant_subquery = participant_query.subquery()
    normalized_status = func.lower(AttendanceModel.status.cast(String))

    total_participants = (
        db.query(func.count())
        .select_from(participant_subquery)
        .scalar()
        or 0
    )

    attendees = (
        db.query(func.count(func.distinct(AttendanceModel.student_id)))
        .join(
            participant_subquery,
            AttendanceModel.student_id == participant_subquery.c.student_id,
        )
        .filter(
            AttendanceModel.event_id == event.id,
            normalized_status.in_(ATTENDED_STATUS_VALUES),
        )
        .scalar()
        or 0
    )

    totals_by_program = {
        program_id: total
        for program_id, total in (
            db.query(
                participant_subquery.c.program_id,
                func.count().label("total"),
            )
            .group_by(participant_subquery.c.program_id)
            .all()
        )
    }
    present_by_program = {
        program_id: present_count
        for program_id, present_count in (
            db.query(
                participant_subquery.c.program_id,
                func.count(func.distinct(AttendanceModel.student_id)).label("present_count"),
            )
            .join(
                AttendanceModel,
                AttendanceModel.student_id == participant_subquery.c.student_id,
            )
            .filter(
                AttendanceModel.event_id == event.id,
                normalized_status == AttendanceStatus.PRESENT.value,
            )
            .group_by(participant_subquery.c.program_id)
            .all()
        )
    }
    late_by_program = {
        program_id: late_count
        for program_id, late_count in (
            db.query(
                participant_subquery.c.program_id,
                func.count(func.distinct(AttendanceModel.student_id)).label("late_count"),
            )
            .join(
                AttendanceModel,
                AttendanceModel.student_id == participant_subquery.c.student_id,
            )
            .filter(
                AttendanceModel.event_id == event.id,
                normalized_status == AttendanceStatus.LATE.value,
            )
            .group_by(participant_subquery.c.program_id)
            .all()
        )
    }
    late_attendees = (
        db.query(func.count(func.distinct(AttendanceModel.student_id)))
        .join(
            participant_subquery,
            AttendanceModel.student_id == participant_subquery.c.student_id,
        )
        .filter(
            AttendanceModel.event_id == event.id,
            normalized_status == AttendanceStatus.LATE.value,
        )
        .scalar()
        or 0
    )

    program_ids_from_participants = {
        program_id
        for program_id in totals_by_program.keys()
        if program_id is not None
    }
    program_ids_for_response = program_ids_from_participants | set(program_ids)

    program_models = []
    if program_ids_for_response:
        program_models = (
            db.query(Program)
            .filter(
                Program.school_id == school_id,
                Program.id.in_(program_ids_for_response),
            )
            .order_by(Program.name.asc())
            .all()
        )

    programs_payload = [{"id": program.id, "name": program.name} for program in program_models]
    breakdown_payload = []

    for program in program_models:
        total = int(totals_by_program.get(program.id, 0) or 0)
        present = int(present_by_program.get(program.id, 0) or 0)
        late = int(late_by_program.get(program.id, 0) or 0)
        absent = max(total - present - late, 0)
        breakdown_payload.append(
            {
                "program": program.name,
                "total": total,
                "present": present,
                "late": late,
                "absent": absent,
            }
        )

    unknown_program_total = int(totals_by_program.get(None, 0) or 0)
    if unknown_program_total > 0:
        unknown_present = int(present_by_program.get(None, 0) or 0)
        unknown_late = int(late_by_program.get(None, 0) or 0)
        breakdown_payload.append(
            {
                "program": "Unassigned",
                "total": unknown_program_total,
                "present": unknown_present,
                "late": unknown_late,
                "absent": max(unknown_program_total - unknown_present - unknown_late, 0),
            }
        )

    absentees = max(int(total_participants) - int(attendees), 0)
    attendance_rate = round((attendees / total_participants) * 100, 2) if total_participants else 0.0

    return AttendanceReportResponse(
        event_name=event.name,
        event_date=event.start_datetime.strftime("%Y-%m-%d"),
        event_location=event.location or "N/A",
        total_participants=int(total_participants),
        attendees=int(attendees),
        late_attendees=int(late_attendees),
        absentees=absentees,
        attendance_rate=attendance_rate,
        programs=programs_payload,
        program_breakdown=breakdown_payload,
    )

# 1. Get all students with basic attendance stats - NOW WITH DATE RANGE FILTER
@router.get("/students/overview", response_model=List[StudentListItem])
async def get_students_attendance_overview(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    department_id: Optional[int] = Query(None),
    program_id: Optional[int] = Query(None),
    # NEW DATE RANGE FILTERS
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    governance_context: Optional[GovernanceUnitType] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get optimized overview of students with attendance stats with date range filtering"""
    
    _ensure_attendance_report_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    allowed_event_ids = _get_event_ids_in_attendance_scope(
        db,
        school_id=school_id,
        governance_units=governance_units,
    )

    try:
        logger.debug(
            "Building student attendance overview",
            extra={
                "start_date": str(start_date) if start_date else None,
                "end_date": str(end_date) if end_date else None,
                "department_id": department_id,
                "program_id": program_id,
                "search": search,
            },
        )
        
        # STEP 1: Simple base query without complex joins
        base_query = (
            db.query(StudentProfile)
            .join(User, StudentProfile.user_id == User.id)
            .filter(User.school_id == school_id)
        )
        base_query = _apply_student_scope_filters(base_query, governance_units)

        # Apply filters BEFORE joins to reduce dataset
        if department_id:
            base_query = base_query.filter(StudentProfile.department_id == department_id)
            
        if program_id:
            base_query = base_query.filter(StudentProfile.program_id == program_id)

        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            base_query = base_query.filter(
                or_(
                    StudentProfile.student_id.ilike(search_filter),
                    func.concat(
                        User.first_name, ' ',
                        func.coalesce(User.middle_name + ' ', ''),
                        User.last_name
                    ).ilike(search_filter)
                )
            )

        # Get total count BEFORE adding joinedload (which can cause issues)
        total_students = base_query.count()
        logger.debug("Student attendance overview matched %s students", total_students)

        # NOW add the relationships we need
        base_query = base_query.options(
            joinedload(StudentProfile.user),
            joinedload(StudentProfile.department),
            joinedload(StudentProfile.program)
        )

        # LIMIT the query early to prevent large dataset issues
        students = base_query.offset(skip).limit(limit).all()
        logger.debug("Loaded %s students for attendance overview page", len(students))
        
        if not students:
            return []

        # STEP 2: Get attendance data in a single query WITH DATE FILTERING
        student_ids = [s.id for s in students]
        
        attendance_stats = {}
        event_counts = {}
        
        try:
            # Build attendance query with date range filtering
            attendance_query = db.query(
                AttendanceModel.student_id,
                func.count(
                    case(
                        (
                            func.lower(AttendanceModel.status.cast(String)).in_(ATTENDED_STATUS_VALUES),
                            1,
                        )
                    )
                ).label('total_attended'),
                func.count(func.distinct(AttendanceModel.event_id)).label('total_events'),
                func.max(AttendanceModel.time_in).label('last_attendance')
            ).join(Event, AttendanceModel.event_id == Event.id).filter(
                AttendanceModel.student_id.in_(student_ids),
                Event.school_id == school_id,
            )
            if governance_units:
                if not allowed_event_ids:
                    logger.debug("Attendance overview matched no in-scope events")
                    attendance_results = []
                else:
                    attendance_query = attendance_query.filter(Event.id.in_(allowed_event_ids))
            
            # Apply date range filters
            if start_date:
                start_datetime = datetime.combine(start_date, datetime.min.time())
                attendance_query = attendance_query.filter(Event.start_datetime >= start_datetime)
                
            if end_date:
                end_datetime = datetime.combine(end_date, datetime.max.time())
                attendance_query = attendance_query.filter(Event.start_datetime <= end_datetime)
            
            if allowed_event_ids or not governance_units:
                attendance_results = attendance_query.group_by(AttendanceModel.student_id).all()
            logger.debug(
                "Attendance overview aggregate query returned %s rows",
                len(attendance_results),
            )
            
            # Process results
            for student_id, total_attended, total_events, last_att in attendance_results:
                attendance_stats[student_id] = {
                    'attended': total_attended,
                    'last_attendance': last_att
                }
                event_counts[student_id] = total_events
                
        except Exception:
            logger.exception("Attendance overview aggregate query failed")
            attendance_stats = {}
            event_counts = {}

        # STEP 3: Build response
        result = []
        for student in students:
            try:
                # Get attendance stats
                stats = attendance_stats.get(student.id, {'attended': 0, 'last_attendance': None})
                attended = stats['attended']
                last_attendance = stats['last_attendance']

                # Get total events from attendance records
                total_events = event_counts.get(student.id, 0)

                # Build name safely
                first_name = getattr(student.user, 'first_name', '') or ''
                middle_name = getattr(student.user, 'middle_name', '') or ''
                last_name = getattr(student.user, 'last_name', '') or ''
                
                middle_part = f"{middle_name} " if middle_name else ""
                full_name = f"{first_name} {middle_part}{last_name}".strip()

                # Calculate attendance rate
                attendance_rate = round((attended / total_events * 100) if total_events > 0 else 0, 2)

                result.append(StudentListItem(
                    id=student.id,
                    student_id=student.student_id,
                    full_name=full_name,
                    department_name=getattr(student.department, 'name', None) if student.department else None,
                    program_name=getattr(student.program, 'name', None) if student.program else None,
                    year_level=student.year_level,
                    total_events=total_events,
                    attendance_rate=attendance_rate,
                    last_attendance=last_attendance
                ))
                
            except Exception:
                logger.exception("Failed to process attendance overview row", extra={"student_id": student.id})
                continue

        logger.debug("Returning %s student attendance overview rows", len(result))
        return result

    except Exception as exc:
        logger.exception("Attendance overview request failed")
        raise HTTPException(500, f"Database error: {str(exc)}") from exc

# 2. Get detailed attendance report for a specific student - ENHANCED DATE FILTERING
@router.get("/students/{student_id}/report", response_model=StudentAttendanceReport)
def get_student_attendance_report(
    student_id: int,
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    # Additional filters
    status: Optional[AttendanceStatus] = Query(None, description="Filter by attendance status"),
    event_type: Optional[str] = Query(None, description="Filter by event type/category"),
    governance_context: Optional[GovernanceUnitType] = Query(None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed attendance report for a specific student with enhanced filtering"""
    
    can_view_own_records = (
        has_any_role(current_user, ["student"])
        and current_user.student_profile is not None
        and current_user.student_profile.id == student_id
    )
    if not can_view_own_records:
        _ensure_attendance_report_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = (
        []
        if can_view_own_records
        else _get_attendance_governance_units(
            db,
            current_user=current_user,
            governance_context=governance_context,
        )
    )
    allowed_event_ids = _get_event_ids_in_attendance_scope(
        db,
        school_id=school_id,
        governance_units=governance_units,
    )

    # Get student
    student = db.query(StudentProfile).options(
        joinedload(StudentProfile.user),
        joinedload(StudentProfile.department),
        joinedload(StudentProfile.program)
    ).join(User, StudentProfile.user_id == User.id).filter(
        StudentProfile.id == student_id,
        User.school_id == school_id,
    ).first()
    
    if not student:
        raise HTTPException(404, "Student not found")
    _ensure_student_in_attendance_scope(student, governance_units)
    
    # Build attendance query with enhanced date filters
    attendances: list[AttendanceModel] = []
    attendance_query = db.query(AttendanceModel).options(
        joinedload(AttendanceModel.event)
    ).join(Event, AttendanceModel.event_id == Event.id).filter(
        AttendanceModel.student_id == student_id,
        Event.school_id == school_id,
    )
    if governance_units:
        if not allowed_event_ids:
            attendances = []
            attendance_query = None
        else:
            attendance_query = attendance_query.filter(Event.id.in_(allowed_event_ids))
    
    # Apply date range filters
    if attendance_query is not None and start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        attendance_query = attendance_query.filter(Event.start_datetime >= start_datetime)
    
    if attendance_query is not None and end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        attendance_query = attendance_query.filter(Event.start_datetime <= end_datetime)
    
    # Apply status filter
    if attendance_query is not None and status:
        attendance_query = attendance_query.filter(AttendanceModel.status == status)
    
    # Apply event type filter (assuming you have event_type or category field in Event model)
    if attendance_query is not None and event_type:
        attendance_query = attendance_query.filter(Event.event_type == event_type)
    
    if attendance_query is not None:
        attendances = attendance_query.order_by(Event.start_datetime.desc()).all()
    
    # Calculate summary statistics
    total_attended = len([a for a in attendances if is_attended_status(a.status)])
    total_late = len(
        [a for a in attendances if normalize_attendance_status(a.status) == AttendanceStatus.LATE.value]
    )
    total_absent = len(
        [a for a in attendances if normalize_attendance_status(a.status) == AttendanceStatus.ABSENT.value]
    )
    total_excused = len(
        [a for a in attendances if normalize_attendance_status(a.status) == AttendanceStatus.EXCUSED.value]
    )
    total_events = len(attendances)
    
    attendance_rate = (total_attended / total_events * 100) if total_events > 0 else 0
    last_attendance = max([a.time_in for a in attendances if a.time_in]) if attendances else None
    
    # Build full name
    middle_name = student.user.middle_name
    full_name = f"{student.user.first_name} {middle_name + ' ' if middle_name else ''}{student.user.last_name}"
    
    # Create summary
    summary = StudentAttendanceSummary(
        student_id=student.student_id,
        student_name=full_name,
        total_events=total_events,
        attended_events=total_attended,
        late_events=total_late,
        absent_events=total_absent,
        excused_events=total_excused,
        attendance_rate=round(attendance_rate, 2),
        last_attendance=last_attendance
    )
    
    # Create detailed records
    attendance_records = []
    for attendance in attendances:
        duration_minutes = None
        if attendance.time_in and attendance.time_out:
            duration_minutes = int((attendance.time_out - attendance.time_in).total_seconds() / 60)
        
        attendance_records.append(StudentAttendanceDetail(
            id=attendance.id,
            event_id=attendance.event_id,
            event_name=attendance.event.name,
            event_location=attendance.event.location,
            event_date=attendance.event.start_datetime,
            time_in=attendance.time_in,
            time_out=attendance.time_out,
            check_in_status=attendance.check_in_status,
            check_out_status=attendance.check_out_status,
            status=attendance.status,
            method=attendance.method,
            notes=attendance.notes,
            duration_minutes=duration_minutes
        ))
    
    # Generate monthly statistics for charts (within date range)
    monthly_stats = {}
    for attendance in attendances:
        if attendance.event and attendance.event.start_datetime:
            month_key = attendance.event.start_datetime.strftime("%Y-%m")
            if month_key not in monthly_stats:
                monthly_stats[month_key] = empty_attendance_status_counts()
            status_value = normalize_attendance_status(attendance.status)
            monthly_stats[month_key][status_value] = monthly_stats[month_key].get(status_value, 0) + 1
    
    # Generate event type statistics (customize based on your event types)
    event_type_stats = {}
    for attendance in attendances:
        if attendance.event:
            event_type = getattr(attendance.event, 'event_type', 'Regular Events')
            event_type_stats[event_type] = event_type_stats.get(event_type, 0) + 1
    
    return StudentAttendanceReport(
        student=summary,
        attendance_records=attendance_records,
        monthly_stats=monthly_stats,
        event_type_stats=event_type_stats
    )

# 3. Get attendance statistics for dashboard/charts - WITH DATE RANGE
@router.get("/students/{student_id}/stats")
def get_student_attendance_stats(
    student_id: int,
    # NEW DATE RANGE FILTERS
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    group_by: Optional[str] = Query("month", description="Group by: month, week, day"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get attendance statistics optimized for charts and visualizations with date filtering"""
    
    can_view_own_records = (
        has_any_role(current_user, ["student"])
        and current_user.student_profile is not None
        and current_user.student_profile.id == student_id
    )
    if not can_view_own_records:
        _ensure_attendance_report_access(db, current_user)
    school_id = get_school_id_or_403(current_user)

    student_in_school = db.query(StudentProfile.id).join(
        User, StudentProfile.user_id == User.id
    ).filter(
        StudentProfile.id == student_id,
        User.school_id == school_id,
    ).first()
    if not student_in_school:
        raise HTTPException(404, "Student not found")

    # Base attendance query with date filtering
    base_query = db.query(AttendanceModel).join(
        Event, AttendanceModel.event_id == Event.id
    ).filter(
        AttendanceModel.student_id == student_id,
        Event.school_id == school_id,
    )
    
    # Apply date range filters
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        base_query = base_query.filter(Event.start_datetime >= start_datetime)
        
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        base_query = base_query.filter(Event.start_datetime <= end_datetime)
    
    # Get attendance with status counts
    status_counts = base_query.with_entities(
        AttendanceModel.status,
        func.count(AttendanceModel.id).label('count')
    ).group_by(AttendanceModel.status).all()
    
    # Get trend data based on group_by parameter
    date_trunc_mapping = {
        "day": "day",
        "week": "week", 
        "month": "month",
        "year": "year"
    }
    
    trunc_period = date_trunc_mapping.get(group_by, "month")
    
    trend_query = base_query.with_entities(
        func.date_trunc(trunc_period, Event.start_datetime).label('period'),
        AttendanceModel.status,
        func.count(AttendanceModel.id).label('count')
    ).filter(
        Event.start_datetime.isnot(None)
    ).group_by(
        func.date_trunc(trunc_period, Event.start_datetime),
        AttendanceModel.status
    ).order_by('period')
    
    trend_results = trend_query.all()
    
    # Get event type breakdown (if you have event types)
    event_type_query = base_query.join(Event).with_entities(
        Event.event_type.label('type'),  # Adjust based on your Event model
        AttendanceModel.status,
        func.count(AttendanceModel.id).label('count')
    ).group_by(Event.event_type, AttendanceModel.status).all()
    
    # Format data for frontend charts
    status_distribution = empty_attendance_status_counts()
    for row in status_counts:
        status_distribution[normalize_attendance_status(row.status)] = int(row.count)

    return {
        "status_distribution": status_distribution,
        "trend_data": [
            {
                "period": row.period.strftime(f"%Y-%m-%d" if group_by == "day" else "%Y-%m" if group_by == "month" else "%Y-%U" if group_by == "week" else "%Y") if row.period else None,
                "status": normalize_attendance_status(row.status),
                "count": row.count
            }
            for row in trend_results
        ],
        "event_type_breakdown": [
            {
                "event_type": row.type or "Unknown",
                "status": normalize_attendance_status(row.status),
                "count": row.count
            }
            for row in event_type_query
        ],
        "date_range": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "group_by": group_by
        }
    }

# 4. NEW: Get attendance summary across all students with date range
@router.get("/summary", response_model=Dict[str, Any])
def get_attendance_summary(
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    department_id: Optional[int] = Query(None),
    program_id: Optional[int] = Query(None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall attendance summary with date range filtering for dashboard"""
    
    _ensure_attendance_report_access(db, current_user)
    school_id = get_school_id_or_403(current_user)

    # Base query
    query = db.query(AttendanceModel).join(
        Event, AttendanceModel.event_id == Event.id
    ).filter(Event.school_id == school_id)
    
    # Apply date filters
    if start_date:
        query = query.filter(Event.start_datetime >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Event.start_datetime <= datetime.combine(end_date, datetime.max.time()))
    
    # Apply department/program filters
    if department_id or program_id:
        query = query.join(StudentProfile, AttendanceModel.student_id == StudentProfile.id).join(
            User, StudentProfile.user_id == User.id
        ).filter(User.school_id == school_id)
        if department_id:
            query = query.filter(StudentProfile.department_id == department_id)
        if program_id:
            query = query.filter(StudentProfile.program_id == program_id)
    
    # Get summary statistics
    total_records = query.count()
    present_count = query.filter(AttendanceModel.status == "present").count()
    late_count = query.filter(AttendanceModel.status == "late").count()
    absent_count = query.filter(AttendanceModel.status == "absent").count()
    excused_count = query.filter(AttendanceModel.status == "excused").count()
    attended_count = present_count + late_count
    
    # Get unique students and events count
    unique_students = query.with_entities(AttendanceModel.student_id).distinct().count()
    unique_events = query.with_entities(AttendanceModel.event_id).distinct().count()
    
    return {
        "summary": {
            "total_attendance_records": total_records,
            "present_count": present_count,
            "late_count": late_count,
            "attended_count": attended_count,
            "absent_count": absent_count,
            "excused_count": excused_count,
            "attendance_rate": round((attended_count / total_records * 100) if total_records > 0 else 0, 2),
            "unique_students": unique_students,
            "unique_events": unique_events
        },
        "filters_applied": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "department_id": department_id,
            "program_id": program_id
        }
    }


# 1. Get current student's attendance
@router.get("/students/me", response_model=List[Attendance])
def get_my_attendance(
    event_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current student's attendance records"""
    # Fixed: Better role checking
    if not has_any_role(current_user, ["student"]) or not current_user.student_profile:
        raise HTTPException(403, "User is not a student")
    school_id = get_school_id_or_403(current_user)

    query = db.query(AttendanceModel).join(
        Event, AttendanceModel.event_id == Event.id
    ).filter(
        AttendanceModel.student_id == current_user.student_profile.id,
        Event.school_id == school_id,
    )
    
    if event_id:
        query = query.filter(AttendanceModel.event_id == event_id)
    
    return query.order_by(AttendanceModel.time_in.desc()).offset(skip).limit(limit).all()

# 2. Face scan attendance - FIXED
@router.post("/face-scan")
def record_face_scan_attendance(
    event_id: int,
    student_id: str,
    current_user: UserModel = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Record attendance via face scan"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    event = _get_event_in_school_or_404(db, event_id, school_id)

    student = db.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(
        StudentProfile.student_id == student_id,
        User.school_id == school_id,
    ).first()
    
    if not student:
        raise HTTPException(404, f"Student {student_id} not found")
    
    active_attendance = _active_attendance_for_student_event(
        db,
        student_profile_id=student.id,
        event_id=event_id,
    )
    if active_attendance is not None:
        sign_out_decision = _get_event_sign_out_decision(event)
        if not sign_out_decision["attendance_allowed"]:
            raise HTTPException(409, sign_out_decision)

        duration_minutes = _complete_attendance_sign_out(
            active_attendance,
            recorded_at=datetime.utcnow(),
        )
        db.commit()
        db.refresh(active_attendance)
        return {
            "message": f"Time out recorded successfully for {student_id}",
            "attendance_id": active_attendance.id,
            "student_id": student_id,
            "time_in": active_attendance.time_in,
            "time_out": active_attendance.time_out,
            "duration_minutes": duration_minutes,
        }

    attendance_decision = _get_event_attendance_decision(event)
    if not attendance_decision["attendance_allowed"]:
        raise HTTPException(409, attendance_decision)

    existing = (
        db.query(AttendanceModel)
        .filter(
            AttendanceModel.student_id == student.id,
            AttendanceModel.event_id == event_id,
        )
        .order_by(AttendanceModel.time_in.desc(), AttendanceModel.id.desc())
        .first()
    )
    if existing and existing.time_out is not None:
        raise HTTPException(400, f"Attendance already exists for student {student_id}")

    scanned_at = datetime.utcnow()
    status_value = attendance_decision["attendance_status"] or "absent"
    
    # Create attendance record
    attendance = AttendanceModel(
        student_id=student.id,
        event_id=event_id,
        time_in=scanned_at,
        method="face_scan",
        status=status_value,
        check_in_status=status_value,
        check_out_status=None,
        verified_by=current_user.id
    )
    
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return {
        "message": "Attendance recorded successfully",
        "attendance_id": attendance.id,
        "student_id": student_id,
        "time_in": attendance.time_in
    }

# 3. Manual attendance - FIXED
@router.post("/manual")
def record_manual_attendance(
    data: ManualAttendanceRequest = Body(...),
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record manual attendance"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    event = _get_event_in_school_or_404(db, data.event_id, school_id)
    _ensure_event_in_attendance_scope(event, governance_units)

    student = db.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(
        StudentProfile.student_id == data.student_id,
        User.school_id == school_id,
    ).first()
    
    if not student:
        raise HTTPException(404, f"Student {data.student_id} not found")
    _ensure_student_in_attendance_scope(student, governance_units)
    _ensure_student_is_event_participant(student, event)
    
    active_attendance = _active_attendance_for_student_event(
        db,
        student_profile_id=student.id,
        event_id=data.event_id,
    )
    if active_attendance is not None:
        sign_out_decision = _get_event_sign_out_decision(event)
        if not sign_out_decision["attendance_allowed"]:
            raise HTTPException(409, sign_out_decision)

        duration_minutes = _complete_attendance_sign_out(
            active_attendance,
            recorded_at=datetime.utcnow(),
        )
        db.commit()
        db.refresh(active_attendance)
        return {
            "message": f"Recorded time out for {data.student_id}",
            "attendance_id": active_attendance.id,
            "action": "time_out",
            "duration_minutes": duration_minutes,
        }

    attendance_decision = _get_event_attendance_decision(event)
    if not attendance_decision["attendance_allowed"]:
        raise HTTPException(409, attendance_decision)

    existing = (
        db.query(AttendanceModel)
        .filter(
            AttendanceModel.student_id == student.id,
            AttendanceModel.event_id == data.event_id,
        )
        .order_by(AttendanceModel.time_in.desc(), AttendanceModel.id.desc())
        .first()
    )
    if existing and existing.time_out is not None:
        raise HTTPException(400, f"Attendance already exists for student {data.student_id}")

    recorded_at = datetime.utcnow()
    status_value = attendance_decision["attendance_status"] or "absent"
    
    # Create attendance record
    attendance = AttendanceModel(
        student_id=student.id,
        event_id=data.event_id,
        time_in=recorded_at,
        method="manual",
        status=status_value,
        check_in_status=status_value,
        check_out_status=None,
        verified_by=current_user.id,
        notes=data.notes or "Pending sign-out."
    )
    
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return {
        "message": f"Recorded attendance for {data.student_id}",
        "attendance_id": attendance.id,
        "action": "time_in",
    }

# 4. Bulk attendance
@router.post("/bulk")
def record_bulk_attendance(
    data: BulkAttendanceRequest,
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record multiple attendances at once"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )

    requested_event_ids = {record.event_id for record in data.records}
    allowed_events = {
        event.id: event
        for event in db.query(Event).filter(
            Event.id.in_(requested_event_ids),
            Event.school_id == school_id,
        ).all()
    }
    event_sync_changed = False
    for event in allowed_events.values():
        sync_result = sync_event_workflow_status(db, event)
        event_sync_changed = event_sync_changed or sync_result.changed
    if event_sync_changed:
        db.commit()

    results = []
    for record in data.records:
        event = allowed_events.get(record.event_id)
        if event is None:
            results.append({"student_id": record.student_id, "status": "event_not_in_school"})
            continue
        if not _event_matches_governance_units(event, governance_units):
            results.append({"student_id": record.student_id, "status": "event_not_in_scope"})
            continue
        attendance_decision = _get_event_attendance_decision(event)
        if not attendance_decision["attendance_allowed"]:
            results.append(
                {
                    "student_id": record.student_id,
                    "status": attendance_decision["reason_code"] or "attendance_not_allowed",
                }
            )
            continue

        student = db.query(StudentProfile).join(
            User, StudentProfile.user_id == User.id
        ).filter(
            StudentProfile.student_id == record.student_id,
            User.school_id == school_id,
        ).first()
        
        if not student:
            results.append({"student_id": record.student_id, "status": "not_found"})
            continue
        if governance_units and not governance_hierarchy_service.governance_units_match_student_scope(
            governance_units,
            department_id=student.department_id,
            program_id=student.program_id,
        ):
            results.append({"student_id": record.student_id, "status": "student_not_in_scope"})
            continue
        try:
            _ensure_student_is_event_participant(student, event)
        except HTTPException:
            results.append({"student_id": record.student_id, "status": "student_not_in_event_scope"})
            continue
            
        existing = db.query(AttendanceModel).filter(
            AttendanceModel.student_id == student.id,
            AttendanceModel.event_id == record.event_id
        ).first()
        
        if existing:
            results.append({"student_id": record.student_id, "status": "exists"})
            continue
            
        recorded_at = datetime.utcnow()
        attendance = AttendanceModel(
            student_id=student.id,
            event_id=record.event_id,
            time_in=recorded_at,
            method="manual",
            status=attendance_decision["attendance_status"] or "absent",
            check_in_status=attendance_decision["attendance_status"] or "absent",
            check_out_status=None,
            verified_by=current_user.id,
            notes=record.notes or "Pending sign-out."
        )
        db.add(attendance)
        results.append({"student_id": record.student_id, "status": "recorded"})
    
    db.commit()
    return {"processed": len(results), "results": results}

# 5. Mark excused
@router.post("/events/{event_id}/mark-excused")
def mark_excused_attendance(
    event_id: int,
    student_ids: List[str],
    reason: str,
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark students as excused for an event"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    event = _get_event_in_school_or_404(db, event_id, school_id)
    _ensure_event_in_attendance_scope(event, governance_units)

    students = db.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(
        StudentProfile.student_id.in_(student_ids),
        User.school_id == school_id,
    ).all()
    
    for student in students:
        _ensure_student_in_attendance_scope(student, governance_units)
        _ensure_student_is_event_participant(student, event)
        attendance = db.query(AttendanceModel).filter(
            AttendanceModel.student_id == student.id,
            AttendanceModel.event_id == event_id
        ).first()
        
        if attendance:
            attendance.status = AttendanceStatus.EXCUSED
            attendance.notes = reason
        else:
            attendance = AttendanceModel(
                student_id=student.id,
                event_id=event_id,
                status=AttendanceStatus.EXCUSED,
                notes=reason,
                method="manual",
                verified_by=current_user.id
            )
            db.add(attendance)
    
    db.commit()
    return {"message": f"Marked {len(students)} students as excused"}

# 6. Get event attendees
@router.get("/events/{event_id}/attendees", response_model=List[Attendance])
def get_event_attendees(
    event_id: int,
    status: Optional[AttendanceStatus] = None,
    skip: int = 0,
    limit: int = 100,
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendees for an event"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    event = _get_event_in_school_or_404(db, event_id, school_id)
    _ensure_event_in_attendance_scope(
        event,
        _get_attendance_governance_units(
            db,
            current_user=current_user,
            governance_context=governance_context,
        ),
    )

    query = db.query(AttendanceModel).filter(
        AttendanceModel.event_id == event_id
    )
    
    if status:
        query = query.filter(AttendanceModel.status == status)
    
    return query.order_by(
        AttendanceModel.status,
        AttendanceModel.time_in
    ).offset(skip).limit(limit).all()


# 4. Time-out recording - FIXED
@router.post("/{attendance_id}/time-out")
def record_time_out(
    attendance_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record time-out for an attendance record"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)

    attendance = db.query(AttendanceModel).join(
        Event, AttendanceModel.event_id == Event.id
    ).filter(
        AttendanceModel.id == attendance_id
    ).filter(
        Event.school_id == school_id
    ).first()
    
    if not attendance:
        raise HTTPException(404, "Attendance record not found")
    _ensure_event_in_attendance_scope(
        attendance.event,
        _get_attendance_governance_units(
            db,
            current_user=current_user,
            governance_context=governance_context,
        ),
    )
    
    if attendance.time_out:
        raise HTTPException(400, "Time-out already recorded")

    sign_out_decision = _get_event_sign_out_decision(attendance.event)
    if not sign_out_decision["attendance_allowed"]:
        raise HTTPException(409, sign_out_decision)

    duration_minutes = _complete_attendance_sign_out(
        attendance,
        recorded_at=datetime.utcnow(),
    )
    db.commit()
    
    return {
        "message": "Time-out recorded successfully",
        "attendance_id": attendance_id,
        "time_in": attendance.time_in,
        "time_out": attendance.time_out,
        "duration_minutes": duration_minutes}

@router.post("/face-scan-timeout")
def record_face_scan_timeout(
    event_id: int,
    student_id: str,
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Record timeout via face scan"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    event = _get_event_in_school_or_404(db, event_id, school_id)
    _ensure_event_in_attendance_scope(event, governance_units)

    # Find student
    student = db.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(
        StudentProfile.student_id == student_id,
        User.school_id == school_id,
    ).first()
    
    if not student:
        raise HTTPException(404, f"Student {student_id} not found")
    _ensure_student_in_attendance_scope(student, governance_units)
    _ensure_student_is_event_participant(student, event)
    
    # Find existing attendance record
    attendance = db.query(AttendanceModel).filter(
        AttendanceModel.student_id == student.id,
        AttendanceModel.event_id == event_id,
        AttendanceModel.time_out.is_(None)  # Only get records without timeout
    ).first()
    
    if not attendance:
        raise HTTPException(404, f"No active attendance found for student {student_id}")
    
    # Check if timeout already recorded
    if attendance.time_out:
        raise HTTPException(400, f"Timeout already recorded for this attendance")

    sign_out_decision = _get_event_sign_out_decision(event)
    if not sign_out_decision["attendance_allowed"]:
        raise HTTPException(409, sign_out_decision)

    duration_minutes = _complete_attendance_sign_out(
        attendance,
        recorded_at=datetime.utcnow(),
    )
    db.commit()
    
    return {
        "message": "Face scan timeout recorded successfully",
        "attendance_id": attendance.id,
        "student_id": student_id,
        "time_in": attendance.time_in,
        "time_out": attendance.time_out,
        "duration_minutes": duration_minutes
    }    

@router.get("/events/{event_id}/attendances", response_model=List[AttendanceWithStudent])
def get_attendances_by_event(
    event_id: int,
    active_only: bool = Query(True, description="Only show active attendances (no time_out)"),
    skip: int = 0,
    limit: int = 100,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get all attendance records for a specific event with student details"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    event = _get_event_in_school_or_404(db, event_id, school_id)
    _ensure_event_in_attendance_scope(event, governance_units)

    query = db.query(
        AttendanceModel,
        StudentProfile.student_id,
        User.first_name,
        User.last_name
    )\
    .join(StudentProfile, AttendanceModel.student_id == StudentProfile.id)\
    .join(User, StudentProfile.user_id == User.id)\
    .join(Event, AttendanceModel.event_id == Event.id)\
    .filter(
        AttendanceModel.event_id == event_id,
        Event.school_id == school_id,
        User.school_id == school_id,
    )
    
    if active_only:
        query = query.filter(AttendanceModel.time_out.is_(None))
    
    results = query.order_by(AttendanceModel.time_in.desc())\
                  .offset(skip)\
                  .limit(limit)\
                  .all()

    return [AttendanceWithStudent(
        attendance=attendance,
        student_id=student_id,
        student_name=f"{first_name} {last_name}"
    ) for attendance, student_id, first_name, last_name in results]

@router.get("/events/{event_id}/attendances/{status}", response_model=List[Attendance])
def get_attendances_by_event_and_status(
    event_id: int,
    status: AttendanceStatus,
    skip: int = 0,
    limit: int = 100,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get attendance records for an event filtered by status"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    event = _get_event_in_school_or_404(db, event_id, school_id)
    _ensure_event_in_attendance_scope(event, governance_units)
    return db.query(AttendanceModel)\
            .join(Event, AttendanceModel.event_id == Event.id)\
            .filter(
                AttendanceModel.event_id == event_id,
                AttendanceModel.status == status,
                Event.school_id == school_id,
            )\
            .order_by(AttendanceModel.time_in.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

@router.get("/events/{event_id}/attendances-with-students", response_model=List[AttendanceWithStudent])
def get_attendances_with_students(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get attendance records with student information"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    event = _get_event_in_school_or_404(db, event_id, school_id)
    _ensure_event_in_attendance_scope(event, governance_units)

    results = db.query(
        AttendanceModel,
        StudentProfile.student_id,
        User.first_name,
        User.last_name
    )\
    .join(StudentProfile, AttendanceModel.student_id == StudentProfile.id)\
    .join(User, StudentProfile.user_id == User.id)\
    .join(Event, AttendanceModel.event_id == Event.id)\
    .filter(
        AttendanceModel.event_id == event_id,
        Event.school_id == school_id,
        User.school_id == school_id,
    )\
    .all()

    return [AttendanceWithStudent(
        attendance=attendance,
        student_id=student_id,
        student_name=f"{first_name} {last_name}"
    ) for attendance, student_id, first_name, last_name in results]

@router.get("/students/records", response_model=List[StudentAttendanceResponse])
def get_all_student_attendance_records(
    student_ids: List[str] = Query(None, description="Filter by specific student IDs"),
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    status: Optional[AttendanceStatus] = Query(None, description="Filter by status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get comprehensive attendance records for students with filtering options
    Requires campus admin, admin, or a governance member with attendance access
    """
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)

    # Base query joining all necessary tables
    query = db.query(
        AttendanceModel,
        StudentProfile.student_id,
        User.first_name,
        User.last_name,
        Event.name.label('event_name')
    ).join(
        StudentProfile, AttendanceModel.student_id == StudentProfile.id
    ).join(
        User, StudentProfile.user_id == User.id
    ).join(
        Event, AttendanceModel.event_id == Event.id
    ).filter(
        User.school_id == school_id,
        Event.school_id == school_id,
    )

    # Apply filters
    if student_ids:
        query = query.filter(StudentProfile.student_id.in_(student_ids))
    if event_id:
        query = query.filter(AttendanceModel.event_id == event_id)
    if status:
        query = query.filter(AttendanceModel.status == status)

    # Execute query
    results = query.order_by(
        StudentProfile.student_id,
        AttendanceModel.time_in.desc()
    ).offset(skip).limit(limit).all()

    # Group results by student
    student_records = {}
    for attendance, student_id, first_name, last_name, event_name in results:
        # Calculate duration if time_out exists
        duration = None
        if attendance.time_out:
            duration = int((attendance.time_out - attendance.time_in).total_seconds() / 60)

        record = StudentAttendanceRecord(
            id=attendance.id,
            event_id=attendance.event_id,
            event_name=event_name,
            time_in=attendance.time_in,
            time_out=attendance.time_out,
            check_in_status=attendance.check_in_status,
            check_out_status=attendance.check_out_status,
            status=attendance.status,
            method=attendance.method,
            notes=attendance.notes,
            duration_minutes=duration
        )

        if student_id not in student_records:
            student_records[student_id] = {
                'student_id': student_id,
                'student_name': f"{first_name} {last_name}",
                'attendances': []
            }
        student_records[student_id]['attendances'].append(record)

    # Convert to response format
    response = []
    for student_id, data in student_records.items():
        response.append(StudentAttendanceResponse(
            student_id=student_id,
            student_name=data['student_name'],
            total_records=len(data['attendances']),
            attendances=data['attendances']
        ))

    return response

@router.get("/students/{student_id}/records", response_model=StudentAttendanceResponse)
def get_student_attendance_records(
    student_id: str,
    event_id: Optional[int] = Query(None),
    status: Optional[AttendanceStatus] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get all attendance records for a specific student"""
    # Permission check - allow students to view their own records
    if has_any_role(current_user, ["student"]) and current_user.student_profile and current_user.student_profile.student_id != student_id:
        raise HTTPException(403, "Can only view your own records")
    school_id = get_school_id_or_403(current_user)

    student = db.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(
        StudentProfile.student_id == student_id,
        User.school_id == school_id,
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    # Query attendances with event names
    query = db.query(
        AttendanceModel,
        Event.name.label('event_name')
    ).join(
        Event, AttendanceModel.event_id == Event.id
    ).filter(
        AttendanceModel.student_id == student.id,
        Event.school_id == school_id,
    )

    if event_id:
        query = query.filter(AttendanceModel.event_id == event_id)
    if status:
        query = query.filter(AttendanceModel.status == status)

    results = query.order_by(
        AttendanceModel.time_in.desc()
    ).offset(skip).limit(limit).all()

    # Process results
    attendances = []
    for attendance, event_name in results:
        duration = None
        if attendance.time_out:
            duration = int((attendance.time_out - attendance.time_in).total_seconds() / 60)

        attendances.append(StudentAttendanceRecord(
            id=attendance.id,
            event_id=attendance.event_id,
            event_name=event_name,
            time_in=attendance.time_in,
            time_out=attendance.time_out,
            check_in_status=attendance.check_in_status,
            check_out_status=attendance.check_out_status,
            status=attendance.status,
            method=attendance.method,
            notes=attendance.notes,
            duration_minutes=duration
        ))

    return StudentAttendanceResponse(
        student_id=student_id,
        student_name=f"{student.user.first_name} {student.user.last_name}",
        total_records=len(attendances),
        attendances=attendances
    )  

@router.get("/me/records", response_model=List[StudentAttendanceResponse])
def get_my_attendance_records(
    current_user: UserModel = Depends(get_current_user),
    event_id: Optional[int] = Query(None),
    status: Optional[AttendanceStatus] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get attendance records for the currently authenticated student
    """
    # Verify the user is a student
    if not current_user.student_profile:
        raise HTTPException(
            status_code=403,
            detail="Only students can access their own attendance records"
        )
    school_id = get_school_id_or_403(current_user)

    student = current_user.student_profile

    # Query attendances with event names
    query = db.query(
        AttendanceModel,
        Event.name.label('event_name')
    ).join(
        Event, AttendanceModel.event_id == Event.id
    ).filter(
        AttendanceModel.student_id == student.id,
        Event.school_id == school_id,
    )

    if event_id:
        query = query.filter(AttendanceModel.event_id == event_id)
    if status:
        query = query.filter(AttendanceModel.status == status)

    results = query.order_by(
        AttendanceModel.time_in.desc()
    ).offset(skip).limit(limit).all()

    # Process results
    attendances = []
    for attendance, event_name in results:
        duration = None
        if attendance.time_out:
            duration = int((attendance.time_out - attendance.time_in).total_seconds() / 60)

        attendances.append(StudentAttendanceRecord(
            id=attendance.id,
            event_id=attendance.event_id,
            event_name=event_name,
            time_in=attendance.time_in,
            time_out=attendance.time_out,
            status=attendance.status,
            method=attendance.method,
            notes=attendance.notes,
            duration_minutes=duration
        ))

    return [StudentAttendanceResponse(
        student_id=student.student_id,
        student_name=f"{current_user.first_name} {current_user.last_name}",
        total_records=len(attendances),
        attendances=attendances
    )]      


@router.post("/mark-absent-no-timeout")
def mark_absent_no_timeout(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark students as absent if they timed in but didn't time out"""
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )

    # Find event
    event = _get_event_in_school_or_404(db, event_id, school_id)
    _ensure_event_in_attendance_scope(event, governance_units)
    
    # Only process completed events
    if event.status != EventStatus.COMPLETED:
        raise HTTPException(400, "Can only mark absent for completed events")
    
    # Find attendances with time_in but no time_out
    attendances_to_update = db.query(AttendanceModel).filter(
        AttendanceModel.event_id == event_id,
        AttendanceModel.time_in.isnot(None),
        AttendanceModel.time_out.is_(None),
        AttendanceModel.status.in_(["present", "late", "absent"]),
    ).all()
    
    updated_count = 0
    for attendance in attendances_to_update:
        attendance.check_out_status = "absent"
        attendance.status, final_note = finalize_completed_attendance_status(
            check_in_status=attendance.check_in_status or attendance.status,
            check_out_status=attendance.check_out_status,
        )
        attendance.notes = (
            f"Auto-marked absent - no sign-out recorded. {final_note or attendance.notes or ''}"
        ).strip()
        updated_count += 1
    
    db.commit()
    
    return {
        "message": f"Marked {updated_count} students as absent",
        "event_id": event_id,
        "updated_count": updated_count
    }    



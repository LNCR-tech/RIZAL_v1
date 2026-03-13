from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, and_, or_, text, String
from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.models.user import User as UserModel
from app.models.attendance import Attendance as AttendanceModel
from app.models.user import StudentProfile
from app.schemas.attendance import AttendanceStatus, Attendance, AttendanceWithStudent, StudentAttendanceRecord, StudentAttendanceResponse, AttendanceReportResponse, StudentAttendanceSummary, StudentAttendanceDetail, StudentAttendanceReport, StudentListItem
from app.models.attendance import Attendance as AttendanceModel
from app.database import get_db
from app.core.security import get_current_user, get_school_id_or_403, has_any_role
from app.models.user import User  # Add this import
from app.models.event import Event, EventStatus  # This imports your Event model
from app.models.program import Program  # This imports your Event model
from app.models.associations import event_program_association  # This imports your Event model
from app.models.department import Department 
from app.models.associations import event_program_association, event_department_association
from app.services.attendance_status import (
    ATTENDED_STATUS_VALUES,
    empty_attendance_status_counts,
    is_attended_status,
    normalize_attendance_status,
    resolve_time_in_status,
)
from app.services.event_time_status import get_attendance_decision
from app.services.event_workflow_status import sync_event_workflow_status


router = APIRouter(prefix="/attendance", tags=["attendance"])


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
        late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
    )
    payload = decision.to_dict()
    for key in ("current_time", "start_time", "end_time", "late_threshold_time"):
        value = payload.get(key)
        if isinstance(value, datetime):
            payload[key] = value.isoformat()
    return payload

# Request models
class ManualAttendanceRequest(BaseModel):
    event_id: int
    student_id: str  # Student ID string
    notes: Optional[str] = None

class BulkAttendanceRequest(BaseModel):
    records: List[ManualAttendanceRequest]

class StudentAttendanceFilter(BaseModel):
    event_id: Optional[int] = None
    status: Optional[AttendanceStatus] = None


def _ensure_event_report_access(current_user: UserModel) -> None:
    if not has_any_role(current_user, ["admin", "ssg", "event-organizer", "event_organizer"]):
        raise HTTPException(403, "Insufficient permissions")


@router.get("/events/{event_id}/report", response_model=AttendanceReportResponse)
def get_event_attendance_report(
    event_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_event_report_access(current_user)
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
            .filter(Program.id.in_(program_ids_for_response))
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get optimized overview of students with attendance stats with date range filtering"""
    
    # Permission check
    if not has_any_role(current_user, ["ssg", "admin", "event-organizer", "event_organizer"]):
        raise HTTPException(403, "Insufficient permissions")
    school_id = get_school_id_or_403(current_user)

    try:
        print("Starting attendance overview query...")
        print(f"Date range filter: {start_date} to {end_date}")
        
        # STEP 1: Simple base query without complex joins
        base_query = (
            db.query(StudentProfile)
            .join(User, StudentProfile.user_id == User.id)
            .filter(User.school_id == school_id)
        )

        # Apply filters BEFORE joins to reduce dataset
        if department_id:
            base_query = base_query.filter(StudentProfile.department_id == department_id)
            print(f"Filtered by department_id: {department_id}")
            
        if program_id:
            base_query = base_query.filter(StudentProfile.program_id == program_id)
            print(f"Filtered by program_id: {program_id}")

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
            print(f"Applied search filter: {search}")

        # Get total count BEFORE adding joinedload (which can cause issues)
        total_students = base_query.count()
        print(f"Total students found: {total_students}")

        # NOW add the relationships we need
        base_query = base_query.options(
            joinedload(StudentProfile.user),
            joinedload(StudentProfile.department),
            joinedload(StudentProfile.program)
        )

        # LIMIT the query early to prevent large dataset issues
        students = base_query.offset(skip).limit(limit).all()
        print(f"Students retrieved: {len(students)}")
        
        if not students:
            return []

        # STEP 2: Get attendance data in a single query WITH DATE FILTERING
        student_ids = [s.id for s in students]
        print(f"Student IDs: {student_ids[:5]}...")  # Show first 5 for debugging
        
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
            
            # Apply date range filters
            if start_date:
                start_datetime = datetime.combine(start_date, datetime.min.time())
                attendance_query = attendance_query.filter(Event.start_datetime >= start_datetime)
                print(f"Applied start_date filter: {start_datetime}")
                
            if end_date:
                end_datetime = datetime.combine(end_date, datetime.max.time())
                attendance_query = attendance_query.filter(Event.start_datetime <= end_datetime)
                print(f"Applied end_date filter: {end_datetime}")
            
            attendance_results = attendance_query.group_by(AttendanceModel.student_id).all()
            
            print(f"Attendance query returned {len(attendance_results)} records")
            
            # Process results
            for student_id, total_attended, total_events, last_att in attendance_results:
                attendance_stats[student_id] = {
                    'attended': total_attended,
                    'last_attendance': last_att
                }
                event_counts[student_id] = total_events
                
        except Exception as e:
            print(f"Error in attendance query: {str(e)}")
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
                
            except Exception as e:
                print(f"Error processing student {student.id}: {str(e)}")
                continue

        print(f"Returning {len(result)} students")
        return result

    except Exception as e:
        print(f"MAIN ERROR in attendance overview: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Database error: {str(e)}")

# 2. Get detailed attendance report for a specific student - ENHANCED DATE FILTERING
@router.get("/students/{student_id}/report", response_model=StudentAttendanceReport)
def get_student_attendance_report(
    student_id: int,
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    # Additional filters
    status: Optional[AttendanceStatus] = Query(None, description="Filter by attendance status"),
    event_type: Optional[str] = Query(None, description="Filter by event type/category"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed attendance report for a specific student with enhanced filtering"""
    
    # Check permissions
    user_roles = {role.role.name for role in current_user.roles}
    if not has_any_role(current_user, ["ssg", "admin", "event-organizer", "event_organizer"]):
        # Students can only view their own records
        if "student" in user_roles and current_user.student_profile:
            if current_user.student_profile.id != student_id:
                raise HTTPException(403, "Can only view your own attendance")
        else:
            raise HTTPException(403, "Insufficient permissions")
    school_id = get_school_id_or_403(current_user)

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
    
    # Build attendance query with enhanced date filters
    attendance_query = db.query(AttendanceModel).options(
        joinedload(AttendanceModel.event)
    ).join(Event, AttendanceModel.event_id == Event.id).filter(
        AttendanceModel.student_id == student_id,
        Event.school_id == school_id,
    )
    
    # Apply date range filters
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        attendance_query = attendance_query.filter(Event.start_datetime >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        attendance_query = attendance_query.filter(Event.start_datetime <= end_datetime)
    
    # Apply status filter
    if status:
        attendance_query = attendance_query.filter(AttendanceModel.status == status)
    
    # Apply event type filter (assuming you have event_type or category field in Event model)
    if event_type:
        attendance_query = attendance_query.filter(Event.event_type == event_type)
    
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
    
    # Check permissions (same as above)
    user_roles = {role.role.name for role in current_user.roles}
    if not has_any_role(current_user, ["ssg", "admin", "event-organizer", "event_organizer"]):
        if "student" in user_roles and current_user.student_profile:
            if current_user.student_profile.id != student_id:
                raise HTTPException(403, "Can only view your own attendance")
        else:
            raise HTTPException(403, "Insufficient permissions")
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
    
    # Permission check
    if not has_any_role(current_user, ["ssg", "admin", "event-organizer", "event_organizer"]):
        raise HTTPException(403, "Insufficient permissions")
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
    # Fixed: Better role checking
    if not has_any_role(current_user, ["ssg"]):
        raise HTTPException(403, "Requires SSG role")
    school_id = get_school_id_or_403(current_user)
    event = _get_event_in_school_or_404(db, event_id, school_id)
    attendance_decision = _get_event_attendance_decision(event)
    if not attendance_decision["attendance_allowed"]:
        raise HTTPException(409, attendance_decision)

    student = db.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(
        StudentProfile.student_id == student_id,
        User.school_id == school_id,
    ).first()
    
    if not student:
        raise HTTPException(404, f"Student {student_id} not found")
    
    # Check for existing attendance
    existing = db.query(AttendanceModel).filter(
        AttendanceModel.student_id == student.id,
        AttendanceModel.event_id == event_id
    ).first()
    
    if existing:
        # Calculate time difference properly
        time_diff = (datetime.utcnow() - existing.time_in).total_seconds()
        if time_diff < 300:  # 5-minute cooldown
            raise HTTPException(400, f"Duplicate scan detected. Last scan was {int(time_diff/60)} minutes ago.")

    scanned_at = datetime.utcnow()
    status_value = attendance_decision["attendance_status"] or resolve_time_in_status(
        event_start=event.start_datetime,
        time_in=scanned_at,
        late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
    )
    
    # Create attendance record
    attendance = AttendanceModel(
        student_id=student.id,
        event_id=event_id,
        time_in=scanned_at,
        method="face_scan",
        status=status_value,
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
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record manual attendance"""
    # Fixed: Better role checking
    if not has_any_role(current_user, ["ssg"]):
        raise HTTPException(403, "Requires SSG role")
    school_id = get_school_id_or_403(current_user)
    event = _get_event_in_school_or_404(db, data.event_id, school_id)
    attendance_decision = _get_event_attendance_decision(event)
    if not attendance_decision["attendance_allowed"]:
        raise HTTPException(409, attendance_decision)

    student = db.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(
        StudentProfile.student_id == data.student_id,
        User.school_id == school_id,
    ).first()
    
    if not student:
        raise HTTPException(404, f"Student {data.student_id} not found")
    
    # Check for existing attendance
    existing = db.query(AttendanceModel).filter(
        AttendanceModel.student_id == student.id,
        AttendanceModel.event_id == data.event_id
    ).first()
    
    if existing:
        raise HTTPException(400, f"Attendance already exists for student {data.student_id}")

    recorded_at = datetime.utcnow()
    status_value = attendance_decision["attendance_status"] or resolve_time_in_status(
        event_start=event.start_datetime,
        time_in=recorded_at,
        late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
    )
    
    # Create attendance record
    attendance = AttendanceModel(
        student_id=student.id,
        event_id=data.event_id,
        time_in=recorded_at,
        method="manual",
        status=status_value,
        verified_by=current_user.id,
        notes=data.notes
    )
    
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return {
        "message": f"Recorded attendance for {data.student_id}",
        "attendance_id": attendance.id}

# 4. Bulk attendance
@router.post("/bulk")
def record_bulk_attendance(
    data: BulkAttendanceRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record multiple attendances at once"""
    if not has_any_role(current_user, ["ssg"]):
        raise HTTPException(403, "Requires SSG role")
    school_id = get_school_id_or_403(current_user)

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
            status=attendance_decision["attendance_status"] or resolve_time_in_status(
                event_start=event.start_datetime,
                time_in=recorded_at,
                late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
            ),
            verified_by=current_user.id,
            notes=record.notes
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
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark students as excused for an event"""
    if not has_any_role(current_user, ["ssg", "admin"]):
        raise HTTPException(403, "Requires SSG/Admin role")
    school_id = get_school_id_or_403(current_user)
    _get_event_in_school_or_404(db, event_id, school_id)

    students = db.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(
        StudentProfile.student_id.in_(student_ids),
        User.school_id == school_id,
    ).all()
    
    for student in students:
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
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendees for an event"""
    if not has_any_role(current_user, ["ssg", "admin"]):
        raise HTTPException(403, "Requires SSG/Admin role")
    school_id = get_school_id_or_403(current_user)
    _get_event_in_school_or_404(db, event_id, school_id)

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
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record time-out for an attendance record"""
    # Check if user has permission
    if not has_any_role(current_user, ["ssg", "admin"]):
        raise HTTPException(403, "Requires SSG or Admin role")
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
    
    if attendance.time_out:
        raise HTTPException(400, "Time-out already recorded")
    
    # Record time-out
    attendance.time_out = datetime.now(timezone.utc)
    db.commit()
    
    # Calculate duration
    duration_seconds = (attendance.time_out - attendance.time_in).total_seconds()
    duration_minutes = int(duration_seconds / 60)
    
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
    current_user: UserModel = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Record timeout via face scan"""
    # Check permissions
    if not has_any_role(current_user, ["ssg"]):
        raise HTTPException(403, "Requires SSG role")
    school_id = get_school_id_or_403(current_user)
    _get_event_in_school_or_404(db, event_id, school_id)

    # Find student
    student = db.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(
        StudentProfile.student_id == student_id,
        User.school_id == school_id,
    ).first()
    
    if not student:
        raise HTTPException(404, f"Student {student_id} not found")
    
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
    
    # Record timeout
    attendance.time_out = datetime.utcnow()
    db.commit()
    
    # Calculate duration
    duration_seconds = (attendance.time_out - attendance.time_in).total_seconds()
    duration_minutes = int(duration_seconds / 60)
    
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
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get all attendance records for a specific event with student details"""
    school_id = get_school_id_or_403(current_user)

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
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get attendance records for an event filtered by status"""
    school_id = get_school_id_or_403(current_user)
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
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get attendance records with student information"""
    school_id = get_school_id_or_403(current_user)

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
    Requires admin or ssg role
    """
    # Check permissions
    if not has_any_role(current_user, ["admin", "ssg"]):
        raise HTTPException(status_code=403, detail="Requires admin or SSG role")
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
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark students as absent if they timed in but didn't time out"""
    # Check permissions
    if not has_any_role(current_user, ["ssg", "admin"]):
        raise HTTPException(403, "Requires SSG or Admin role")
    school_id = get_school_id_or_403(current_user)

    # Find event
    event = _get_event_in_school_or_404(db, event_id, school_id)
    
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
        attendance.status = "absent"
        attendance.notes = f"Auto-marked absent - no time-out recorded. {attendance.notes or ''}".strip()
        updated_count += 1
    
    db.commit()
    
    return {
        "message": f"Marked {updated_count} students as absent",
        "event_id": event_id,
        "updated_count": updated_count
    }    



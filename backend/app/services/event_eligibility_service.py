from typing import Optional, Tuple
from app.models.user import StudentProfile
from app.models.event import Event, EventTargetScope
from app.models.governance_hierarchy import GovernanceMember
from app.schemas.user import StudentStatus

def is_student_eligible_for_event(
    student: StudentProfile,
    event: Event,
    db=None,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Determine if a student is eligible to participate in an event.
    
    Eligibility rules:
    1. Student must belong to the same school as the event.
    2. Student must have student_status = ACTIVE.
    3. Student must match at least one event_target (Phase 4).
    4. Fallback to legacy targeting (departments/programs) for backward compatibility.
    
    Returns:
        (eligible, error_code, error_message)
    """
    # 1. School check
    if student.school_id != event.school_id:
        return (
            False, 
            "STUDENT_SCHOOL_MISMATCH", 
            "Student belongs to a different school than the event."
        )

    # 2. Status check
    if student.student_status != StudentStatus.ACTIVE:
        return (
            False, 
            "STUDENT_NOT_ACTIVE", 
            f"Only ACTIVE students can participate. Current status: {student.student_status}"
        )

    # 3. Governance membership check — if the event is tied to a governance unit,
    # only active members of that unit may attend.
    governance_unit_id = getattr(event, "governance_unit_id", None)
    if governance_unit_id is not None:
        if db is None:
            return (
                False,
                "MEMBERS_ONLY_CHECK_UNAVAILABLE",
                "Cannot verify governance membership without a database session.",
            )
        is_member = (
            db.query(GovernanceMember)
            .filter(
                GovernanceMember.governance_unit_id == governance_unit_id,
                GovernanceMember.user_id == student.user_id,
                GovernanceMember.is_active.is_(True),
            )
            .first()
        ) is not None
        if not is_member:
            return (
                False,
                "NOT_A_GOVERNANCE_MEMBER",
                "This event is restricted to governance unit members only.",
            )

    # 4. Targeted Audience check
    event_targets = getattr(event, "event_targets", [])
    
    if event_targets:
        matched = False
        for target in event_targets:
            scope = target.scope_type
            if scope == EventTargetScope.ALL:
                matched = True
            elif scope == EventTargetScope.YEAR_LEVEL:
                if student.year_level == target.year_level:
                    matched = True
            elif scope == EventTargetScope.DEPARTMENT:
                if student.department_id == target.department_id:
                    matched = True
            elif scope == EventTargetScope.COURSE:
                if student.program_id == target.course_id:
                    matched = True
            elif scope == EventTargetScope.DEPARTMENT_YEAR:
                if student.department_id == target.department_id and student.year_level == target.year_level:
                    matched = True
            elif scope == EventTargetScope.COURSE_YEAR:
                if student.program_id == target.course_id and student.year_level == target.year_level:
                    matched = True
            
            if matched:
                break
        
        if not matched:
            return (
                False, 
                "STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE", 
                "Student is not included in this event scope."
            )
        
        return True, None, None

    # Fallback to legacy targeting (Phase 3 and below)
    event_program_ids = {program.id for program in getattr(event, "programs", [])}
    event_department_ids = {department.id for department in getattr(event, "departments", [])}
    
    # If no targets at all (legacy data), check if it's truly empty
    if not event_program_ids and not event_department_ids:
        # If the event is from Phase 4+ it SHOULD have had an ALL target created by default.
        # If it's missing here, it might be a legacy event or a data inconsistency.
        # For legacy events, empty scope meant school-wide.
        # But Phase 5 requirements say "Event must have at least one valid event_target."
        # We'll allow legacy school-wide events but log a warning if needed?
        # Actually, let's return True to preserve old behavior for old events.
        return True, None, None

    if event_program_ids and student.program_id not in event_program_ids:
        return (
            False, 
            "STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE", 
            "Student is outside the event program scope."
        )
    
    if event_department_ids and student.department_id not in event_department_ids:
        return (
            False, 
            "STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE", 
            "Student is outside the event department scope."
        )

    return True, None, None

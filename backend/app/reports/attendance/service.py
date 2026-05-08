"""Business logic for attendance event-level reports."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_school_id_or_403, has_any_role
from app.models.governance_hierarchy import GovernanceUnitType
from app.models.user import User as UserModel
from app.schemas.attendance import (
    Attendance,
    AttendanceCompletionState,
    AttendanceReportResponse,
    AttendanceStatus,
    AttendanceWithStudent,
)
from app.services.event_workflow_status import sync_event_workflow_status
from app.routers.attendance.shared import (
    _attendance_display_status_value,
    _attendance_is_valid_value,
    _attendance_matches_status_filter,
    _ensure_attendance_operator_access,
    _ensure_event_in_attendance_scope,
    _ensure_event_report_access,
    _get_attendance_governance_units,
    _get_event_in_school_or_404,
    _serialize_attendance_model,
    _serialize_attendance_with_student,
)

from . import queries


def get_event_attendance_report(
    db: Session,
    *,
    event_id: int,
    year_level: int | None = None,
    department_id: int | None = None,
    program_id: int | None = None,
    status_filter: AttendanceStatus | None = None,
    governance_context: GovernanceUnitType | None,
    current_user: UserModel,
) -> AttendanceReportResponse:
    _ensure_event_report_access(db, current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    actor_school_id = None
    if not (has_any_role(current_user, ["admin"]) and getattr(current_user, "school_id", None) is None):
        actor_school_id = get_school_id_or_403(current_user)

    event = queries.get_event_for_report(
        db,
        event_id=event_id,
        actor_school_id=actor_school_id,
    )
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

    participant_subquery = queries.build_participant_subquery(
        db,
        school_id=school_id,
        event=event,
        year_level=year_level,
        department_id=department_id,
        program_id=program_id,
    )
    total_participants = queries.count_participants_from_subquery(db, participant_subquery)
    totals_by_program = queries.count_participants_by_program_from_subquery(db, participant_subquery)
    
    # Get expected student IDs for absent calculation
    expected_student_ids = {
        row[0] for row in db.query(participant_subquery.c.student_id).all()
    }

    attendance_rows = queries.list_event_attendance_rows_for_event_report(
        db,
        event_id=event.id,
        year_level=year_level,
        department_id=department_id,
        program_id=program_id,
    )

    latest_attendance_by_student: dict[int, tuple] = {}
    for attendance, p_id in attendance_rows:
        latest_attendance_by_student.setdefault(attendance.student_id, (attendance, p_id))

    attendees = 0
    late_attendees = 0
    incomplete_attendees = 0
    signed_out_attendees = 0
    no_sign_out_attendees = 0
    expected_attendees_who_showed_up = 0
    present_by_program: dict[int | None, int] = {}
    late_by_program: dict[int | None, int] = {}
    incomplete_by_program: dict[int | None, int] = {}

    for attendance, p_id in latest_attendance_by_student.values():
        display_status = _attendance_display_status_value(attendance)
        
        if status_filter and display_status != status_filter.value:
            continue

        is_valid = _attendance_is_valid_value(attendance)
        is_completed = attendance.completion_state == AttendanceCompletionState.COMPLETED.value
        is_expected = attendance.student_id in expected_student_ids

        if is_valid:
            attendees += 1
            if is_expected:
                expected_attendees_who_showed_up += 1

            if is_completed:
                signed_out_attendees += 1
            else:
                no_sign_out_attendees += 1

            if display_status == AttendanceStatus.PRESENT.value:
                present_by_program[p_id] = present_by_program.get(p_id, 0) + 1
            elif display_status == AttendanceStatus.LATE.value:
                late_attendees += 1
                late_by_program[p_id] = late_by_program.get(p_id, 0) + 1
        elif display_status == AttendanceStatus.INCOMPLETE.value:
            incomplete_attendees += 1
            no_sign_out_attendees += 1
            if is_expected:
                expected_attendees_who_showed_up += 1
            incomplete_by_program[p_id] = incomplete_by_program.get(p_id, 0) + 1

    program_ids_from_participants = {
        p_id
        for p_id in totals_by_program.keys()
        if p_id is not None
    }
    
    target_program_ids = [t.course_id for t in event.event_targets if t.course_id]
    legacy_program_ids = [p.id for p in event.programs]
    program_ids_for_response = program_ids_from_participants | set(target_program_ids) | set(legacy_program_ids)
    
    program_models = queries.list_program_models(
        db,
        school_id=school_id,
        program_ids=program_ids_for_response,
    )

    programs_payload = [{"id": p.id, "name": p.name} for p in program_models]
    breakdown_payload = []
    for p in program_models:
        total = int(totals_by_program.get(p.id, 0) or 0)
        present = int(present_by_program.get(p.id, 0) or 0)
        late = int(late_by_program.get(p.id, 0) or 0)
        incomplete = int(incomplete_by_program.get(p.id, 0) or 0)
        absent = max(total - present - late - incomplete, 0)
        breakdown_payload.append(
            {
                "program": p.name,
                "total": total,
                "present": present,
                "late": late,
                "incomplete": incomplete,
                "absent": absent,
            }
        )

    unknown_program_total = int(totals_by_program.get(None, 0) or 0)
    if unknown_program_total > 0:
        unknown_present = int(present_by_program.get(None, 0) or 0)
        unknown_late = int(late_by_program.get(None, 0) or 0)
        unknown_incomplete = int(incomplete_by_program.get(None, 0) or 0)
        breakdown_payload.append(
            {
                "program": "Unassigned",
                "total": unknown_program_total,
                "present": unknown_present,
                "late": unknown_late,
                "incomplete": unknown_incomplete,
                "absent": max(
                    unknown_program_total - unknown_present - unknown_late - unknown_incomplete,
                    0,
                ),
            }
        )

    absentees = max(int(total_participants) - int(expected_attendees_who_showed_up), 0)
    attendance_rate = round((expected_attendees_who_showed_up / total_participants) * 100, 2) if total_participants else 0.0

    return AttendanceReportResponse(
        event_name=event.name,
        event_date=event.start_datetime.strftime("%Y-%m-%d"),
        event_location=event.location or "N/A",
        total_participants=int(total_participants),
        attendees=int(attendees),
        late_attendees=int(late_attendees),
        incomplete_attendees=int(incomplete_attendees),
        signed_out_attendees=signed_out_attendees,
        no_sign_out_attendees=no_sign_out_attendees,
        absentees=absentees,
        attendance_rate=attendance_rate,
        programs=programs_payload,
        program_breakdown=breakdown_payload,
    )


def get_event_attendees(
    db: Session,
    *,
    event_id: int,
    year_level: int | None = None,
    department_id: int | None = None,
    program_id: int | None = None,
    status: AttendanceStatus | None,
    skip: int,
    limit: int,
    governance_context: GovernanceUnitType | None,
    current_user: UserModel,
) -> list[Attendance]:
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

    participant_subquery = queries.build_participant_subquery(
        db,
        school_id=school_id,
        event=event,
        year_level=year_level,
        department_id=department_id,
        program_id=program_id,
    )
    
    attendances = queries.list_event_attendance_rows_for_report(
        db,
        event_id=event_id,
        participant_subquery=participant_subquery,
    )
    
    # Extract only the attendance models from the tuples
    attendance_models = [row[0] for row in attendances]
    
    filtered = [attendance for attendance in attendance_models if _attendance_matches_status_filter(attendance, status)]
    return [
        _serialize_attendance_model(attendance)
        for attendance in filtered[skip : skip + limit]
    ]


def get_attendances_by_event(
    db: Session,
    *,
    event_id: int,
    active_only: bool,
    year_level: int | None = None,
    department_id: int | None = None,
    program_id: int | None = None,
    skip: int,
    limit: int,
    governance_context: GovernanceUnitType | None,
    current_user: UserModel,
) -> list[AttendanceWithStudent]:
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    event = _get_event_in_school_or_404(db, event_id, school_id)
    _ensure_event_in_attendance_scope(event, governance_units)

    results = queries.list_event_attendance_with_students(
        db,
        event_id=event_id,
        school_id=school_id,
        active_only=active_only,
        year_level=year_level,
        department_id=department_id,
        program_id=program_id,
        skip=skip,
        limit=limit,
    )
    return [
        _serialize_attendance_with_student(
            attendance,
            student_id=student_id,
            student_name=f"{first_name} {last_name}",
        )
        for attendance, student_id, first_name, last_name in results
    ]


def get_attendances_by_event_and_status(
    db: Session,
    *,
    event_id: int,
    status: AttendanceStatus,
    skip: int,
    limit: int,
    governance_context: GovernanceUnitType | None,
    current_user: UserModel,
) -> list[Attendance]:
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    event = _get_event_in_school_or_404(db, event_id, school_id)
    _ensure_event_in_attendance_scope(event, governance_units)

    attendances = queries.list_event_attendance_rows_for_status(
        db,
        event_id=event_id,
        school_id=school_id,
    )
    filtered = [attendance for attendance in attendances if _attendance_matches_status_filter(attendance, status)]
    return [_serialize_attendance_model(attendance) for attendance in filtered[skip : skip + limit]]


def get_attendances_with_students(
    db: Session,
    *,
    event_id: int,
    governance_context: GovernanceUnitType | None,
    current_user: UserModel,
) -> list[AttendanceWithStudent]:
    _ensure_attendance_operator_access(db, current_user)
    school_id = get_school_id_or_403(current_user)
    governance_units = _get_attendance_governance_units(
        db,
        current_user=current_user,
        governance_context=governance_context,
    )
    event = _get_event_in_school_or_404(db, event_id, school_id)
    _ensure_event_in_attendance_scope(event, governance_units)

    results = queries.list_event_attendance_with_students(
        db,
        event_id=event_id,
        school_id=school_id,
        active_only=None,
    )
    return [
        _serialize_attendance_with_student(
            attendance,
            student_id=student_id,
            student_name=f"{first_name} {last_name}",
        )
        for attendance, student_id, first_name, last_name in results
    ]


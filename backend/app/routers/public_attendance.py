"""Use: Handles unauthenticated public attendance kiosk APIs for the login page.
Where to use: Use this through the FastAPI app when the public login page needs nearby events or multi-face attendance scans.
Role: Router layer. It receives HTTP requests, applies public kiosk limits, and returns API responses.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.rate_limit import build_public_rule, client_ip_identity, enforce_rate_limit
from app.core.timezones import utc_now
from app.models.event import Event as EventModel, EventStatus as ModelEventStatus
from app.models.school import School as SchoolModel
from app.schemas.public_attendance import (
    PublicAttendanceEventSummary,
    PublicAttendanceFaceOutcome,
    PublicAttendanceMultiFaceScanRequest,
    PublicAttendanceMultiFaceScanResponse,
    PublicAttendanceNearbyEventsRequest,
    PublicAttendanceNearbyEventsResponse,
)
from app.services.attendance_face_scan import (
    build_outcome_liveness_payload,
    get_registered_face_candidates_for_event,
    get_registered_face_candidates_for_school,
    persist_public_attendance_scan,
    resolve_face_match_scope,
    resolve_face_match_scope_with_pgvector,
    resolve_public_attendance_phase,
    student_display_name,
)
from app.services.event_geolocation import verify_event_geolocation, verify_event_geolocation_for_attendance
from app.services.event_time_status import get_attendance_decision, get_event_timezone, get_sign_out_decision
from app.services.face_recognition import FaceRecognitionService
from app.services.event_workflow_status import sync_event_workflow_status


router = APIRouter(prefix="/public-attendance", tags=["public-attendance"])
face_service = FaceRecognitionService()
settings = get_settings()
PUBLIC_SCAN_REQUEST_MIN_INTERVAL_SECONDS = 0.75
# Keep a tiny in-memory throttle so one kiosk/browser cannot hammer the same
# event scan endpoint multiple times per second inside a single app process.
_PUBLIC_SCAN_REQUEST_TIMESTAMPS: dict[str, float] = {}


def _ensure_public_attendance_enabled() -> None:
    """Stop public kiosk routes when the feature is disabled in config."""
    if not settings.public_attendance_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public attendance kiosk is disabled.",
        )


def _get_public_event_or_404(db: Session, event_id: int) -> EventModel:
    """Load one kiosk-visible event, refresh its workflow state, or raise an HTTP error."""
    event = (
        db.query(EventModel)
        .options(
            joinedload(EventModel.school),
            joinedload(EventModel.departments),
            joinedload(EventModel.programs),
        )
        .join(SchoolModel, EventModel.school_id == SchoolModel.id)
        .filter(
            EventModel.id == event_id,
            SchoolModel.active_status.is_(True),
        )
        .first()
    )
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    # Public kiosk requests should not depend on beat having already updated the
    # row, so resync the workflow status against the current clock on read.
    sync_result = sync_event_workflow_status(db, event)
    if sync_result.changed:
        db.commit()
        db.refresh(event)
    if event.status == ModelEventStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event is cancelled.")
    return event


def _event_scope_label(event: EventModel) -> str:
    """Build the short scope label shown on the kiosk for one event."""
    department_names = [department.name for department in event.departments]
    program_names = [program.name for program in event.programs]
    if not department_names and not program_names:
        return "Campus-wide"
    if program_names:
        return ", ".join(program_names)
    return ", ".join(department_names)


def _event_phase_message(event: EventModel, phase: str) -> str:
    """Return the user-facing kiosk message for the event's active attendance phase."""
    if phase == "sign_out":
        return get_sign_out_decision(
            start_time=event.start_datetime,
            end_time=event.end_datetime,
            early_check_in_minutes=getattr(event, "early_check_in_minutes", 0),
            late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
            sign_out_grace_minutes=getattr(event, "sign_out_grace_minutes", 0),
            sign_out_open_delay_minutes=getattr(event, "sign_out_open_delay_minutes", 0),
            sign_out_override_until=getattr(event, "sign_out_override_until", None),
            present_until_override_at=getattr(event, "present_until_override_at", None),
            late_until_override_at=getattr(event, "late_until_override_at", None),
        ).message

    return get_attendance_decision(
        start_time=event.start_datetime,
        end_time=event.end_datetime,
        early_check_in_minutes=getattr(event, "early_check_in_minutes", 0),
        late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
        sign_out_grace_minutes=getattr(event, "sign_out_grace_minutes", 0),
        sign_out_open_delay_minutes=getattr(event, "sign_out_open_delay_minutes", 0),
        sign_out_override_until=getattr(event, "sign_out_override_until", None),
        present_until_override_at=getattr(event, "present_until_override_at", None),
        late_until_override_at=getattr(event, "late_until_override_at", None),
    ).message


def _request_throttle_key(request: Request, event_id: int) -> str:
    """Group rapid scan requests by client host and event so the kiosk can throttle them."""
    client_host = request.client.host if request.client else "anonymous"
    return f"{client_host}:{event_id}"


def _enforce_public_scan_throttle(request: Request, event_id: int) -> None:
    """Reject repeated public scan requests that arrive too quickly for one client/event pair."""
    now = time.monotonic()
    key = _request_throttle_key(request, event_id)
    last_timestamp = _PUBLIC_SCAN_REQUEST_TIMESTAMPS.get(key)
    if (
        last_timestamp is not None
        and PUBLIC_SCAN_REQUEST_MIN_INTERVAL_SECONDS > 0
        and now - last_timestamp < PUBLIC_SCAN_REQUEST_MIN_INTERVAL_SECONDS
    ):
        retry_after = max(0.0, PUBLIC_SCAN_REQUEST_MIN_INTERVAL_SECONDS - (now - last_timestamp))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "public_scan_throttled",
                "message": "The kiosk is already processing a recent scan. Please wait briefly.",
                "retry_after_seconds": round(retry_after, 3),
            },
        )
    _PUBLIC_SCAN_REQUEST_TIMESTAMPS[key] = now


def _ensure_face_runtime_ready(mode: str, *, context: str) -> None:
    face_service.ensure_face_runtime_ready(mode=mode, context=context)


@router.post("/events/nearby", response_model=PublicAttendanceNearbyEventsResponse)
def list_nearby_public_events(
    payload: PublicAttendanceNearbyEventsRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """List nearby public-kiosk events that are inside the caller's live geofence and active window."""
    _ensure_public_attendance_enabled()
    enforce_rate_limit(build_public_rule(), f"{client_ip_identity(request)}:nearby", request=request)

    timezone = get_event_timezone()
    now_local = datetime.now(timezone).replace(tzinfo=None, microsecond=0)
    lookahead_limit = now_local + timedelta(hours=settings.public_attendance_event_lookahead_hours)
    recent_cutoff = now_local - timedelta(hours=settings.public_attendance_event_lookahead_hours)

    # First fetch events that are broadly eligible for the public kiosk, then
    # apply the caller's live geolocation and attendance-window checks below.
    events = (
        db.query(EventModel)
        .options(
            joinedload(EventModel.school),
            joinedload(EventModel.departments),
            joinedload(EventModel.programs),
        )
        .join(SchoolModel, EventModel.school_id == SchoolModel.id)
        .filter(
            SchoolModel.active_status.is_(True),
            EventModel.geo_latitude.isnot(None),
            EventModel.geo_longitude.isnot(None),
            EventModel.geo_radius_m.isnot(None),
            EventModel.start_datetime <= lookahead_limit,
            EventModel.end_datetime >= recent_cutoff,
        )
        .order_by(EventModel.start_datetime.asc(), EventModel.id.asc())
        .all()
    )

    matched_events: list[PublicAttendanceEventSummary] = []
    changed = False
    for event in events:
        # Nearby-event discovery also nudges stale workflow state forward so the
        # kiosk can still behave correctly even if scheduled sync is delayed.
        sync_result = sync_event_workflow_status(db, event)
        changed = changed or sync_result.changed
        if event.status in {ModelEventStatus.CANCELLED, ModelEventStatus.COMPLETED}:
            continue

        phase = resolve_public_attendance_phase(event)
        if phase is None:
            continue

        try:
            geo_response = verify_event_geolocation(
                event,
                latitude=payload.latitude,
                longitude=payload.longitude,
                accuracy_m=payload.accuracy_m,
            )
        except HTTPException:
            continue

        if not geo_response.ok:
            continue

        school_name = (
            event.school.school_name
            if event.school is not None and event.school.school_name
            else (event.school.name if event.school is not None else "Campus")
        )
        matched_events.append(
            PublicAttendanceEventSummary(
                id=event.id,
                school_id=event.school_id,
                school_name=school_name,
                name=event.name,
                location=event.location,
                start_datetime=event.start_datetime,
                end_datetime=event.end_datetime,
                geo_radius_m=float(event.geo_radius_m or 0),
                distance_m=geo_response.distance_m,
                effective_distance_m=geo_response.effective_distance_m,
                accuracy_m=geo_response.accuracy_m,
                attendance_phase=phase,
                phase_message=_event_phase_message(event, phase),
                scope_label=_event_scope_label(event),
                departments=[department.name for department in event.departments],
                programs=[program.name for program in event.programs],
            )
        )

    if changed:
        db.commit()

    matched_events.sort(
        key=lambda event: (
            0 if event.attendance_phase == "sign_in" else 1,
            event.distance_m,
            event.start_datetime,
            event.id,
        )
    )
    return PublicAttendanceNearbyEventsResponse(
        events=matched_events,
        scan_cooldown_seconds=settings.public_attendance_scan_cooldown_seconds,
    )


@router.post("/events/{event_id}/multi-face-scan", response_model=PublicAttendanceMultiFaceScanResponse)
def scan_public_attendance_event(
    event_id: int,
    payload: PublicAttendanceMultiFaceScanRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Process one kiosk frame, classify each detected face, and persist valid attendance scans."""
    _ensure_public_attendance_enabled()
    enforce_rate_limit(build_public_rule(), f"{client_ip_identity(request)}:public-scan", request=request)
    _enforce_public_scan_throttle(request, event_id)

    event = _get_public_event_or_404(db, event_id)
    phase = resolve_public_attendance_phase(event)
    if phase is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance is not active for this event.",
        )

    # Nearby-event lookup is only discovery. The write path rechecks the stricter
    # attendance geofence here before any scan result can change attendance data.
    geo_response = verify_event_geolocation_for_attendance(
        event,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_m=payload.accuracy_m,
    )

    _ensure_face_runtime_ready(mode="group", context="public_attendance_multi_face_scan")
    image_bytes = face_service.decode_base64_image(payload.image_base64)
    try:
        probes = face_service.analyze_faces_from_bytes(
            image_bytes,
            enforce_liveness=True,
            liveness_threshold_override=settings.public_attendance_liveness_threshold,
            max_faces=settings.public_attendance_max_faces_per_frame,
            mode="group",
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        message = (
            "No face was detected in the current frame."
            if "No face detected" in detail
            else detail
        )
        return PublicAttendanceMultiFaceScanResponse(
            event_id=event.id,
            event_phase=phase,
            message=message,
            scan_cooldown_seconds=settings.public_attendance_scan_cooldown_seconds,
            geo=geo_response,
            outcomes=[],
        )

    event_candidates = None
    school_candidates = None
    seen_student_ids: set[int] = set()
    cooldown_student_ids = {
        student_id.strip()
        for student_id in payload.cooldown_student_ids
        if student_id and student_id.strip()
    }
    outcomes: list[PublicAttendanceFaceOutcome] = []

    # Process each detected face in a strict order: reject spoof/unencodable
    # faces first, then classify the match, then persist only valid scan hits.
    for probe in probes:
        if probe.error_code == "spoof_detected":
            outcomes.append(
                PublicAttendanceFaceOutcome(
                    action="liveness_failed",
                    reason_code="spoof_detected",
                    message="Live face verification failed for one detected face.",
                    liveness=build_outcome_liveness_payload(probe.liveness),
                )
            )
            continue

        if probe.encoding is None:
            outcomes.append(
                PublicAttendanceFaceOutcome(
                    action="no_match",
                    reason_code="encoding_unavailable",
                    message="A detected face could not be encoded for verification.",
                    liveness=build_outcome_liveness_payload(probe.liveness),
                )
            )
            continue

        vector_match = resolve_face_match_scope_with_pgvector(
            db,
            face_service=face_service,
            encoding=probe.encoding,
            event=event,
            threshold=payload.threshold,
            mode="group",
        )
        if vector_match is not None:
            match_scope, student, match = vector_match
        else:
            if event_candidates is None:
                event_candidates = get_registered_face_candidates_for_event(db, event)
            # Event-scoped candidates decide whether a face is actually eligible
            # for this event. School-wide candidates let us tell "known student,
            # wrong scope" apart from "no registered student matched this face".
            if school_candidates is None:
                school_candidates = (
                    event_candidates
                    if not event.departments and not event.programs
                    else get_registered_face_candidates_for_school(db, event.school_id)
                )
            match_scope, student, match = resolve_face_match_scope(
                face_service=face_service,
                encoding=probe.encoding,
                event_candidates=event_candidates,
                school_candidates=school_candidates,
                threshold=payload.threshold,
                mode="group",
            )
        if match_scope == "no_match" or student is None or match.candidate is None:
            outcomes.append(
                PublicAttendanceFaceOutcome(
                    action="no_match",
                    reason_code="no_matching_student",
                    message="No registered student match was found for one detected face.",
                    distance=round(match.distance, 6) if match.distance != float("inf") else None,
                    confidence=round(match.confidence, 6),
                    threshold=round(match.threshold, 6),
                    liveness=build_outcome_liveness_payload(probe.liveness),
                )
            )
            continue

        if match_scope == "out_of_scope":
            outcomes.append(
                PublicAttendanceFaceOutcome(
                    action="out_of_scope",
                    reason_code="student_not_in_event_scope",
                    message="A registered student was detected, but they are not eligible for this event scope.",
                    distance=round(match.distance, 6),
                    confidence=round(match.confidence, 6),
                    threshold=round(match.threshold, 6),
                    liveness=build_outcome_liveness_payload(probe.liveness),
                )
            )
            continue

        if student.student_id in cooldown_student_ids:
            outcomes.append(
                PublicAttendanceFaceOutcome(
                    action="cooldown_skipped",
                    reason_code="client_cooldown_active",
                    message="This student is still inside the kiosk cooldown window.",
                    student_id=student.student_id,
                    student_name=student_display_name(student),
                    distance=round(match.distance, 6),
                    confidence=round(match.confidence, 6),
                    threshold=round(match.threshold, 6),
                    liveness=build_outcome_liveness_payload(probe.liveness),
                )
            )
            continue

        if student.id in seen_student_ids:
            outcomes.append(
                PublicAttendanceFaceOutcome(
                    action="duplicate_face",
                    reason_code="duplicate_face_in_frame",
                    message="The same student was detected more than once in the same frame.",
                    student_id=student.student_id,
                    student_name=student_display_name(student),
                    distance=round(match.distance, 6),
                    confidence=round(match.confidence, 6),
                    threshold=round(match.threshold, 6),
                    liveness=build_outcome_liveness_payload(probe.liveness),
                )
            )
            continue

        seen_student_ids.add(student.id)
        persistence = persist_public_attendance_scan(
            db,
            event=event,
            student=student,
            phase=phase,
            scanned_at=utc_now(),
            geo_response=geo_response,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy_m=payload.accuracy_m,
            liveness=probe.liveness,
        )
        outcomes.append(
            PublicAttendanceFaceOutcome(
                action=persistence.action,
                reason_code=persistence.reason_code,
                message=persistence.message,
                student_id=student.student_id,
                student_name=student_display_name(student),
                attendance_id=persistence.attendance_id,
                distance=round(match.distance, 6),
                confidence=round(match.confidence, 6),
                threshold=round(match.threshold, 6),
                liveness=build_outcome_liveness_payload(probe.liveness),
                time_in=persistence.time_in,
                time_out=persistence.time_out,
                duration_minutes=persistence.duration_minutes,
            )
        )

    return PublicAttendanceMultiFaceScanResponse(
        event_id=event.id,
        event_phase=phase,
        message="Public attendance scan processed successfully.",
        scan_cooldown_seconds=settings.public_attendance_scan_cooldown_seconds,
        geo=geo_response,
        outcomes=outcomes,
    )

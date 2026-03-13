from __future__ import annotations

from datetime import datetime
import math

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user_with_roles, get_school_id_or_403, has_any_role
from app.database import get_db
from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event as EventModel, EventStatus as ModelEventStatus
from app.models.user import StudentProfile, User as UserModel
from app.schemas.event import EventLocationVerificationResponse
from app.schemas.face_recognition import (
    Base64ImageRequest,
    FaceAttendanceScanRequest,
    FaceAttendanceScanResponse,
    FaceRegistrationResponse,
    FaceVerificationResponse,
)
from app.services.face_recognition import FaceCandidate, FaceRecognitionService
from app.services.attendance_status import (
    finalize_completed_attendance_status,
)
from app.services.event_geolocation import (
    find_attendance_geolocation_travel_risk,
    verify_event_geolocation_for_attendance,
)
from app.services.event_time_status import get_attendance_decision
from app.services.event_workflow_status import sync_event_workflow_status


router = APIRouter(prefix="/face", tags=["face-recognition"])
face_service = FaceRecognitionService()


def _student_display_name(student: StudentProfile) -> str:
    user = student.user
    if user is None:
        return student.student_id or f"Student {student.id}"
    full_name = " ".join(
        part.strip()
        for part in [user.first_name or "", user.middle_name or "", user.last_name or ""]
        if part and part.strip()
    ).strip()
    return full_name or student.student_id or f"Student {student.id}"


def _require_student_profile(current_user: UserModel) -> StudentProfile:
    profile = getattr(current_user, "student_profile", None)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users with a student profile can register a student face.",
        )
    return profile


def _get_school_event_or_404(db: Session, event_id: int, school_id: int) -> EventModel:
    event = (
        db.query(EventModel)
        .filter(EventModel.id == event_id, EventModel.school_id == school_id)
        .first()
    )
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    sync_result = sync_event_workflow_status(db, event)
    if sync_result.changed:
        db.commit()
        db.refresh(event)
    if event.status == ModelEventStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event is cancelled.")
    return event


def _attendance_time_window_detail(event: EventModel) -> dict[str, object]:
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


def _attendance_scan_error_detail(
    *,
    code: str,
    message: str,
    **extra: object,
) -> dict[str, object]:
    detail: dict[str, object] = {
        "code": code,
        "message": message,
    }
    detail.update(extra)
    return detail


def _student_candidates_for_school(db: Session, school_id: int) -> list[tuple[StudentProfile, FaceCandidate]]:
    students = (
        db.query(StudentProfile)
        .join(UserModel, StudentProfile.user_id == UserModel.id)
        .filter(
            UserModel.school_id == school_id,
            StudentProfile.face_encoding.isnot(None),
            StudentProfile.is_face_registered.is_(True),
        )
        .all()
    )

    candidates: list[tuple[StudentProfile, FaceCandidate]] = []
    for student in students:
        if not student.face_encoding:
            continue
        candidates.append(
            (
                student,
                FaceCandidate(
                    identifier=student.id,
                    label=_student_display_name(student),
                    encoding_bytes=bytes(student.face_encoding),
                ),
            )
        )
    return candidates


@router.post("/register", response_model=FaceRegistrationResponse)
def register_face_from_base64(
    payload: Base64ImageRequest,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    profile = _require_student_profile(current_user)
    image_bytes = face_service.decode_base64_image(payload.image_base64)
    encoding, liveness = face_service.extract_encoding_from_bytes(
        image_bytes,
        require_single_face=True,
        enforce_liveness=True,
    )

    profile.update_face_encoding(face_service.encoding_to_bytes(encoding))
    profile.registration_complete = True
    db.commit()
    db.refresh(profile)

    return FaceRegistrationResponse(
        message="Face registered successfully.",
        student_id=profile.student_id,
        liveness=liveness.to_dict(),
    )


@router.post("/register-upload", response_model=FaceRegistrationResponse)
async def register_face_from_upload(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    profile = _require_student_profile(current_user)
    image_bytes = await file.read()
    encoding, liveness = face_service.extract_encoding_from_bytes(
        image_bytes,
        require_single_face=True,
        enforce_liveness=True,
    )

    profile.update_face_encoding(face_service.encoding_to_bytes(encoding))
    profile.registration_complete = True
    db.commit()
    db.refresh(profile)

    return FaceRegistrationResponse(
        message="Face registered successfully.",
        student_id=profile.student_id,
        liveness=liveness.to_dict(),
    )


@router.post("/verify", response_model=FaceVerificationResponse)
def verify_face_against_registered_students(
    payload: Base64ImageRequest,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    school_id = get_school_id_or_403(current_user)
    image_bytes = face_service.decode_base64_image(payload.image_base64)
    encoding, liveness = face_service.extract_encoding_from_bytes(
        image_bytes,
        require_single_face=True,
        enforce_liveness=True,
    )

    candidates = _student_candidates_for_school(db, school_id)
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered student faces found in this school.",
        )

    match = face_service.find_best_match(
        encoding,
        [candidate for _, candidate in candidates],
    )
    if not match.matched or match.candidate is None:
        return FaceVerificationResponse(
            match_found=False,
            distance=round(match.distance, 6) if math.isfinite(match.distance) else None,
            confidence=round(match.confidence, 6),
            threshold=round(match.threshold, 6),
            liveness=liveness.to_dict(),
        )

    student_lookup = {
        candidate.identifier: student
        for student, candidate in candidates
    }
    student = student_lookup.get(match.candidate.identifier)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Matched student could not be loaded.",
        )

    return FaceVerificationResponse(
        match_found=True,
        student_id=student.student_id,
        student_name=_student_display_name(student),
        distance=round(match.distance, 6),
        confidence=round(match.confidence, 6),
        threshold=round(match.threshold, 6),
        liveness=liveness.to_dict(),
    )


@router.post("/face-scan-with-recognition", response_model=FaceAttendanceScanResponse)
def record_attendance_from_face_scan(
    payload: FaceAttendanceScanRequest,
    current_user: UserModel = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    actor_is_staff_scan = has_any_role(current_user, ["ssg", "admin"])
    actor_is_student_self_scan = (
        not actor_is_staff_scan and has_any_role(current_user, ["student"])
    )

    if not actor_is_staff_scan and not actor_is_student_self_scan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student, SSG, or admin access is required for face attendance scans.",
        )

    school_id = get_school_id_or_403(current_user)
    event = _get_school_event_or_404(db, payload.event_id, school_id)
    current_student_profile = (
        _require_student_profile(current_user) if actor_is_student_self_scan else None
    )
    if (
        actor_is_student_self_scan
        and current_student_profile is not None
        and not bool(current_student_profile.is_face_registered)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Register your student face before signing in to an event.",
        )

    image_bytes = face_service.decode_base64_image(payload.image_base64)
    encoding, liveness = face_service.extract_encoding_from_bytes(
        image_bytes,
        require_single_face=True,
        enforce_liveness=True,
    )

    candidates = _student_candidates_for_school(db, school_id)
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered student faces found in this school.",
        )

    match = face_service.find_best_match(
        encoding,
        [candidate for _, candidate in candidates],
        threshold=payload.threshold,
    )
    if not match.matched or match.candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching student found.",
        )

    student_lookup = {
        candidate.identifier: student
        for student, candidate in candidates
    }
    student = student_lookup.get(match.candidate.identifier)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Matched student could not be resolved.",
        )

    if (
        actor_is_student_self_scan
        and current_student_profile is not None
        and student.id != current_student_profile.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The live face does not match the currently signed-in student account.",
        )

    geo_response = verify_event_geolocation_for_attendance(
        event,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_m=payload.accuracy_m,
    )

    scanned_at = datetime.utcnow()
    if (
        geo_response is not None
        and payload.latitude is not None
        and payload.longitude is not None
    ):
        travel_risk = find_attendance_geolocation_travel_risk(
            db,
            student_profile_id=student.id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            scanned_at=scanned_at,
        )
        if travel_risk is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_attendance_scan_error_detail(
                    code="implausible_travel_speed",
                    message=(
                        "Location verification failed because the travel pattern "
                        "looks unrealistic."
                    ),
                    distance_m=round(travel_risk.distance_m, 3),
                    elapsed_s=round(travel_risk.elapsed_s, 3),
                    speed_mps=round(travel_risk.speed_mps, 3),
                ),
            )

    active_attendance = (
        db.query(AttendanceModel)
        .filter(
            AttendanceModel.student_id == student.id,
            AttendanceModel.event_id == event.id,
            AttendanceModel.time_out.is_(None),
        )
        .order_by(AttendanceModel.time_in.desc(), AttendanceModel.id.desc())
        .first()
    )

    if active_attendance is not None:
        active_attendance.time_out = scanned_at
        finalized_status, finalized_note = finalize_completed_attendance_status(
            event_start=event.start_datetime,
            event_end=event.end_datetime,
            time_in=active_attendance.time_in,
            time_out=active_attendance.time_out,
            late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
        )
        active_attendance.status = finalized_status
        active_attendance.notes = finalized_note
        db.commit()
        db.refresh(active_attendance)
        duration_minutes = int(
            max(
                0,
                (active_attendance.time_out - active_attendance.time_in).total_seconds() / 60,
            )
        )
        return FaceAttendanceScanResponse(
            action="timeout",
            student_id=student.student_id,
            student_name=_student_display_name(student),
            attendance_id=active_attendance.id,
            distance=round(match.distance, 6),
            confidence=round(match.confidence, 6),
            threshold=round(match.threshold, 6),
            liveness=liveness.to_dict(),
            geo=geo_response,
            time_out=active_attendance.time_out,
            duration_minutes=duration_minutes,
            message=(
                "Check-out recorded successfully."
                if finalized_status == "present"
                else "Check-out recorded successfully. Attendance was marked late based on the event late threshold."
                if finalized_status == "late"
                else "Check-out recorded, but the attendance was marked absent because it did not align with the event schedule."
            ),
        )

    completed_attendance = (
        db.query(AttendanceModel)
        .filter(
            AttendanceModel.student_id == student.id,
            AttendanceModel.event_id == event.id,
        )
        .order_by(AttendanceModel.time_in.desc(), AttendanceModel.id.desc())
        .first()
    )
    if completed_attendance is not None and completed_attendance.time_out is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance has already been completed for this student and event.",
        )

    attendance_decision = get_attendance_decision(
        start_time=event.start_datetime,
        end_time=event.end_datetime,
        late_threshold_minutes=getattr(event, "late_threshold_minutes", 0),
    )
    if not attendance_decision.attendance_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_attendance_scan_error_detail(
                code=attendance_decision.reason_code or "attendance_not_allowed",
                message=attendance_decision.message,
                **_attendance_time_window_detail(event),
            ),
        )

    attendance = AttendanceModel(
        student_id=student.id,
        event_id=event.id,
        time_in=scanned_at,
        method="face_scan",
        status=attendance_decision.attendance_status or "absent",
        verified_by=current_user.id,
        notes="Pending sign-out.",
        geo_distance_m=geo_response.distance_m if geo_response else None,
        geo_effective_distance_m=geo_response.effective_distance_m if geo_response else None,
        geo_latitude=payload.latitude,
        geo_longitude=payload.longitude,
        geo_accuracy_m=payload.accuracy_m,
        liveness_label=str(liveness.label),
        liveness_score=float(liveness.score),
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    time_in_message = (
        "Check-in recorded successfully. Sign out before the event ends to complete your attendance."
        if attendance_decision.attendance_status == "present"
        else "Check-in recorded successfully, but it is already beyond the late threshold. Sign out before the event ends to finalize attendance."
    )

    return FaceAttendanceScanResponse(
        action="time_in",
        student_id=student.student_id,
        student_name=_student_display_name(student),
        attendance_id=attendance.id,
        distance=round(match.distance, 6),
        confidence=round(match.confidence, 6),
        threshold=round(match.threshold, 6),
        liveness=liveness.to_dict(),
        geo=geo_response,
        time_in=attendance.time_in,
        message=time_in_message,
    )

"""Use: Handles security center features and privileged account checks API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs security center features and privileged account checks features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Callable

from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.timezones import utc_now
from app.core.rate_limit import build_face_rule, enforce_rate_limit, user_identity
from app.core.security import (
    ALGORITHM,
    SECRET_KEY,
    decode_token_to_token_data,
    get_current_admin_or_campus_admin,
    get_current_application_user,
    oauth2_scheme,
)
from app.core.dependencies import get_db
from app.models.face_recognition import UserFaceRecognitionProfile
from app.models.platform_features import UserSession
from app.models.user import User
from app.schemas.face_recognition import (
    Base64ImageRequest,
    SecurityFaceLivenessResponse,
    SecurityFaceReferenceResponse,
    SecurityFaceStatusResponse,
    SecurityFaceVerificationRequest,
    SecurityFaceVerificationResponse,
)
from app.schemas.security import (
    DeleteFaceReferenceResponse,
    LoginHistoryItem,
    RevokeOtherSessionsResponse,
    RevokeSessionResponse,
    UserSessionItem,
)
from app.services.auth_session import issue_full_access_token_response
from app.services.security_service import (
    list_active_sessions,
    list_login_history_for_actor,
    record_login_history,
    revoke_other_sessions,
    revoke_session,
)
from app.services.user_preference_service import get_or_create_user_security_setting
from app.services.face_recognition import FaceRecognitionService
from app.services.face_recognition import resolve_face_verification_error_message

router = APIRouter(prefix="/auth/security", tags=["security"])
face_service = FaceRecognitionService()
FACE_STATUS_TIMEOUT_SECONDS = 1.5
_face_runtime_status_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="face-runtime-status",
)
_anti_spoof_status_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="anti-spoof-status",
)
_StatusProbe = Callable[[], tuple[bool, str | None]]
_RuntimeStatusProbe = Callable[[], dict[str, object]]


def _runtime_status_fallback(
    *,
    mode: str,
    state: str,
    reason: str,
    last_error: str | None = None,
) -> dict[str, object]:
    return {
        "state": state,
        "ready": False,
        "reason": reason,
        "last_error": last_error,
        "provider_target": "CPUExecutionProvider",
        "mode": mode,
        "initialized_at": None,
        "warmup_started_at": None,
        "warmup_finished_at": None,
        "model_construction_duration_ms": None,
        "prepare_duration_ms": None,
        "warmup_duration_ms": None,
        "init_duration_ms": None,
    }


def _extract_current_jti(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        return str(jti) if jti else None
    except JWTError:
        return None


def _require_current_mfa_reference(profile: UserFaceRecognitionProfile) -> None:
    """Reject legacy admin face references that were enrolled with the old provider."""
    expected_provider = face_service.embedding_provider_for_mode("mfa")
    if (profile.provider or "").strip().lower() != expected_provider:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Your saved face reference uses a legacy provider. "
                "Delete it and enroll a new ArcFace reference before verifying."
            ),
        )


def _run_status_probe_with_timeout(
    probe: _StatusProbe,
    *,
    executor: ThreadPoolExecutor,
    timeout_reason: str,
    error_reason: str,
) -> tuple[bool, str | None]:
    """Return one status probe result without letting the route hang."""
    future = executor.submit(probe)
    try:
        ready, reason = future.result(timeout=FACE_STATUS_TIMEOUT_SECONDS)
        return bool(ready), reason
    except FutureTimeoutError:
        future.cancel()
        return False, timeout_reason
    except Exception:
        future.cancel()
        return False, error_reason


def _run_runtime_status_probe_with_timeout(
    probe: _RuntimeStatusProbe,
    *,
    executor: ThreadPoolExecutor,
    mode: str,
) -> dict[str, object]:
    future = executor.submit(probe)
    try:
        payload = future.result(timeout=FACE_STATUS_TIMEOUT_SECONDS)
        reason_value = payload.get("reason")
        return {
            "state": str(payload.get("state", "initializing")),
            "ready": bool(payload.get("ready")),
            "reason": (
                str(reason_value)
                if reason_value is not None
                else "insightface_warming_up"
            ),
            "last_error": (
                str(payload.get("last_error"))
                if payload.get("last_error") is not None
                else None
            ),
            "provider_target": str(payload.get("provider_target", "CPUExecutionProvider")),
            "mode": str(payload.get("mode") or mode),
            "initialized_at": payload.get("initialized_at"),
            "warmup_started_at": payload.get("warmup_started_at"),
            "warmup_finished_at": payload.get("warmup_finished_at"),
            "model_construction_duration_ms": payload.get("model_construction_duration_ms"),
            "prepare_duration_ms": payload.get("prepare_duration_ms"),
            "warmup_duration_ms": payload.get("warmup_duration_ms"),
            "init_duration_ms": payload.get("init_duration_ms"),
        }
    except FutureTimeoutError:
        future.cancel()
        return _runtime_status_fallback(
            mode=mode,
            state="initializing",
            reason="insightface_warming_up",
        )
    except Exception:
        future.cancel()
        return _runtime_status_fallback(
            mode=mode,
            state="failed",
            reason="insightface_initialization_failed",
            last_error="runtime_status_probe_error",
        )


@router.get("/sessions", response_model=list[UserSessionItem])
def get_active_sessions(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    current_jti = _extract_current_jti(token)
    sessions = list_active_sessions(db, actor_user_id=current_user.id)
    return [
        UserSessionItem(
            id=item.id,
            token_jti=item.token_jti,
            ip_address=item.ip_address,
            user_agent=item.user_agent,
            created_at=item.created_at,
            last_seen_at=item.last_seen_at,
            revoked_at=item.revoked_at,
            expires_at=item.expires_at,
            is_current=(current_jti is not None and item.token_jti == current_jti),
        )
        for item in sessions
    ]


@router.post("/sessions/{session_id}/revoke", response_model=RevokeSessionResponse)
def revoke_user_session(
    session_id: str,
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    revoked = revoke_session(
        db,
        session_id=session_id,
        actor_user_id=current_user.id,
        allow_self=True,
    )
    if not revoked:
        raise HTTPException(status_code=404, detail="Session not found")
    db.commit()
    return RevokeSessionResponse(session_id=session_id, revoked=True)


@router.post("/sessions/revoke-others", response_model=RevokeOtherSessionsResponse)
def revoke_all_other_sessions(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    current_jti = _extract_current_jti(token)
    current_session_id = None
    if current_jti:
        current_session = (
            db.query(UserSession)
            .filter(
                UserSession.user_id == current_user.id,
                UserSession.token_jti == current_jti,
            )
            .first()
        )
        if current_session is not None:
            current_session_id = current_session.id
    count = revoke_other_sessions(
        db,
        actor_user_id=current_user.id,
        current_session_id=current_session_id,
    )
    db.commit()
    return {"revoked_count": count}


@router.get("/login-history", response_model=list[LoginHistoryItem])
def get_login_history(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    rows = list_login_history_for_actor(db, actor=current_user, limit=limit)
    return rows


@router.get("/face-status", response_model=SecurityFaceStatusResponse)
def get_face_status(
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    privileged_face_verification_enabled = (
        get_settings().privileged_face_verification_enabled
    )
    security_setting = get_or_create_user_security_setting(db, user=current_user)
    profile = (
        db.query(UserFaceRecognitionProfile)
        .filter(UserFaceRecognitionProfile.user_id == current_user.id)
        .first()
    )
    runtime_status = _run_runtime_status_probe_with_timeout(
        lambda: face_service.face_runtime_status(mode="mfa"),
        executor=_face_runtime_status_executor,
        mode="mfa",
    )
    face_runtime_ready = bool(runtime_status["ready"])
    face_runtime_reason = str(runtime_status.get("reason") or "insightface_warming_up")
    anti_spoof_ready, anti_spoof_reason = _run_status_probe_with_timeout(
        face_service.anti_spoof_status,
        executor=_anti_spoof_status_executor,
        timeout_reason="session_unavailable",
        error_reason="session_unavailable",
    )
    return SecurityFaceStatusResponse(
        user_id=current_user.id,
        face_verification_required=bool(
            privileged_face_verification_enabled and security_setting.mfa_enabled
        ),
        face_reference_enrolled=profile is not None,
        provider=(
            profile.provider
            if profile is not None
            else face_service.embedding_provider_for_mode("mfa")
        ),
        updated_at=(profile.updated_at if profile is not None else None),
        last_verified_at=(profile.last_verified_at if profile is not None else None),
        liveness_enabled=True,
        face_runtime_ready=face_runtime_ready,
        face_runtime_reason=face_runtime_reason,
        face_runtime_state=str(runtime_status["state"]),
        face_runtime_last_error=(
            str(runtime_status["last_error"])
            if runtime_status.get("last_error") is not None
            else None
        ),
        face_runtime_provider_target=str(runtime_status["provider_target"]),
        face_runtime_mode=str(runtime_status["mode"]) if runtime_status.get("mode") is not None else None,
        face_runtime_initialized_at=runtime_status.get("initialized_at"),
        face_runtime_warmup_started_at=runtime_status.get("warmup_started_at"),
        face_runtime_warmup_finished_at=runtime_status.get("warmup_finished_at"),
        face_runtime_model_construction_duration_ms=runtime_status.get(
            "model_construction_duration_ms"
        ),
        face_runtime_prepare_duration_ms=runtime_status.get("prepare_duration_ms"),
        face_runtime_warmup_duration_ms=runtime_status.get("warmup_duration_ms"),
        face_runtime_init_duration_ms=runtime_status.get("init_duration_ms"),
        anti_spoof_ready=anti_spoof_ready,
        anti_spoof_reason=anti_spoof_reason,
        live_capture_required=True,
    )


@router.post("/face-liveness", response_model=SecurityFaceLivenessResponse)
def check_face_liveness(
    payload: Base64ImageRequest,
    request: Request,
    current_user: User = Depends(get_current_admin_or_campus_admin),
):
    enforce_rate_limit(build_face_rule(), f"{user_identity(current_user)}:face-liveness", request=request)
    face_service.ensure_face_runtime_ready(mode="mfa", context="security_face_liveness")
    image_bytes = face_service.decode_base64_image(payload.image_base64)
    rgb_image = face_service.load_rgb_from_bytes(image_bytes)
    liveness = face_service.check_liveness(rgb_image, mode="mfa")
    return SecurityFaceLivenessResponse(**liveness.to_dict())


@router.post("/face-reference", response_model=SecurityFaceReferenceResponse)
def save_face_reference(
    payload: Base64ImageRequest,
    request: Request,
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    enforce_rate_limit(build_face_rule(), f"{user_identity(current_user)}:face-reference", request=request)
    face_service.ensure_face_runtime_ready(mode="mfa", context="security_face_reference")
    image_bytes = face_service.decode_base64_image(payload.image_base64)
    try:
        encoding, liveness = face_service.extract_encoding_from_bytes(
            image_bytes,
            require_single_face=True,
            enforce_liveness=True,
            mode="mfa",
        )
    except HTTPException as exc:
        normalized_error = resolve_face_verification_error_message(exc.detail)
        if normalized_error is None:
            raise
        status_code, message = normalized_error
        raise HTTPException(status_code=status_code, detail=message) from exc

    profile = (
        db.query(UserFaceRecognitionProfile)
        .filter(UserFaceRecognitionProfile.user_id == current_user.id)
        .first()
    )
    if profile is None:
        profile = UserFaceRecognitionProfile(
            user_id=current_user.id,
            face_encoding=face_service.encoding_to_bytes(encoding),
            provider=face_service.embedding_provider_for_mode("mfa"),
            reference_image_sha256=face_service.compute_image_sha256(image_bytes),
        )
        db.add(profile)
    else:
        profile.face_encoding = face_service.encoding_to_bytes(encoding)
        profile.provider = face_service.embedding_provider_for_mode("mfa")
        profile.reference_image_sha256 = face_service.compute_image_sha256(image_bytes)

    db.commit()
    db.refresh(profile)

    return SecurityFaceReferenceResponse(
        user_id=current_user.id,
        face_reference_enrolled=True,
        provider=profile.provider,
        updated_at=profile.updated_at,
        liveness=liveness.to_dict(),
    )


@router.delete("/face-reference", response_model=DeleteFaceReferenceResponse)
def delete_face_reference(
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(UserFaceRecognitionProfile)
        .filter(UserFaceRecognitionProfile.user_id == current_user.id)
        .first()
    )
    if profile is not None:
        db.delete(profile)
        db.commit()
    return {"user_id": current_user.id, "face_reference_enrolled": False}


@router.post("/face-verify", response_model=SecurityFaceVerificationResponse)
def verify_face_reference(
    payload: SecurityFaceVerificationRequest,
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    enforce_rate_limit(build_face_rule(), f"{user_identity(current_user)}:face-verify", request=request)
    face_service.ensure_face_runtime_ready(mode="mfa", context="security_face_verify")
    profile = (
        db.query(UserFaceRecognitionProfile)
        .filter(UserFaceRecognitionProfile.user_id == current_user.id)
        .first()
    )
    if profile is None or not profile.face_encoding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No face reference is enrolled for this account.",
        )
    _require_current_mfa_reference(profile)

    image_bytes = face_service.decode_base64_image(payload.image_base64)
    try:
        encoding, liveness = face_service.extract_encoding_from_bytes(
            image_bytes,
            require_single_face=True,
            enforce_liveness=True,
            mode="mfa",
        )
    except HTTPException as exc:
        normalized_error = resolve_face_verification_error_message(exc.detail)
        if normalized_error is None:
            raise
        status_code, message = normalized_error
        raise HTTPException(status_code=status_code, detail=message) from exc
    comparison = face_service.compare_encodings(
        encoding,
        face_service.encoding_from_bytes(
            bytes(profile.face_encoding),
            dtype=face_service.settings.face_embedding_dtype,
            dimension=face_service.settings.face_embedding_dim,
            normalized=True,
        ),
        threshold=payload.threshold,
        mode="mfa",
    )
    token_data = decode_token_to_token_data(token)
    issued_session: dict[str, object | None] | None = None

    if comparison.matched:
        profile.last_verified_at = utc_now()
        if token_data.face_pending:
            issued_session = issue_full_access_token_response(
                db=db,
                user=current_user,
                request=request,
                expires_minutes=token_data.session_duration_minutes,
            )
            record_login_history(
                db,
                email_attempted=current_user.email,
                user=current_user,
                success=True,
                auth_method="face_verification",
                request=request,
            )
        db.commit()
        db.refresh(profile)

    return SecurityFaceVerificationResponse(
        matched=comparison.matched,
        distance=round(comparison.distance, 6),
        confidence=round(comparison.confidence, 6),
        threshold=round(comparison.threshold, 6),
        liveness=liveness.to_dict(),
        verified_at=(profile.last_verified_at if comparison.matched else None),
        access_token=(
            str(issued_session["access_token"])
            if issued_session is not None and issued_session.get("access_token") is not None
            else None
        ),
        token_type=(
            str(issued_session["token_type"])
            if issued_session is not None and issued_session.get("token_type") is not None
            else None
        ),
        session_id=(
            str(issued_session["session_id"])
            if issued_session is not None and issued_session.get("session_id") is not None
            else None
        ),
        face_verification_pending=(
            bool(issued_session.get("face_verification_pending"))
            if issued_session is not None
            else bool(token_data.face_pending and not comparison.matched)
        ),
    )


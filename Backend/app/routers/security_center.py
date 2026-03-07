from __future__ import annotations

from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import ALGORITHM, SECRET_KEY, get_current_user_with_roles, oauth2_scheme
from app.database import get_db
from app.models.platform_features import UserSession
from app.models.user import User
from app.schemas.security import (
    LoginHistoryItem,
    MfaStatusResponse,
    MfaStatusUpdate,
    RevokeSessionResponse,
    UserSessionItem,
)
from app.services.security_service import (
    get_or_create_security_setting,
    list_active_sessions,
    list_login_history_for_actor,
    revoke_other_sessions,
    revoke_session,
)

router = APIRouter(prefix="/auth/security", tags=["security"])


def _extract_current_jti(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        return str(jti) if jti else None
    except JWTError:
        return None


@router.get("/mfa-status", response_model=MfaStatusResponse)
def get_mfa_status(
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    setting = get_or_create_security_setting(db, current_user)
    db.commit()
    db.refresh(setting)
    return MfaStatusResponse(
        user_id=current_user.id,
        mfa_enabled=setting.mfa_enabled,
        trusted_device_days=setting.trusted_device_days,
        updated_at=setting.updated_at,
    )


@router.put("/mfa-status", response_model=MfaStatusResponse)
def update_mfa_status(
    payload: MfaStatusUpdate,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    setting = get_or_create_security_setting(db, current_user)
    setting.mfa_enabled = payload.mfa_enabled
    if payload.trusted_device_days is not None:
        setting.trusted_device_days = payload.trusted_device_days
    db.commit()
    db.refresh(setting)
    return MfaStatusResponse(
        user_id=current_user.id,
        mfa_enabled=setting.mfa_enabled,
        trusted_device_days=setting.trusted_device_days,
        updated_at=setting.updated_at,
    )


@router.get("/sessions", response_model=list[UserSessionItem])
def get_active_sessions(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user_with_roles),
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
    current_user: User = Depends(get_current_user_with_roles),
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


@router.post("/sessions/revoke-others")
def revoke_all_other_sessions(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user_with_roles),
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
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    rows = list_login_history_for_actor(db, actor=current_user, limit=limit)
    return rows

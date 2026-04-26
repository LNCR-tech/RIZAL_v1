"""Use: Contains the main backend rules for security center actions and session tracking.
Where to use: Use this from routers, workers, or other services when security center actions and session tracking logic is needed.
Role: Service layer. It keeps business logic out of the route files.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Iterable, Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.timezones import ensure_utc, utc_now
from app.models.platform_features import LoginHistory, UserSession
from app.models.user import User


def _normalize_role_name(role_name: str) -> str:
    normalized = (role_name or "").strip().lower().replace(" ", "-").replace("_", "-")
    if normalized in {"school-it", "campus-admin"}:
        return "campus-admin"
    return normalized


def _request_ip(request: Optional[Request]) -> str | None:
    if request is None or request.client is None:
        return None
    return request.client.host


def _request_agent(request: Optional[Request]) -> str | None:
    if request is None:
        return None
    return request.headers.get("user-agent")


def _normalize_role_names(user: User) -> set[str]:
    normalized = set()
    for user_role in getattr(user, "roles", []):
        role_name = getattr(getattr(user_role, "role", None), "name", "")
        role_key = _normalize_role_name(role_name)
        if role_key:
            normalized.add(role_key)
    return normalized


def record_login_history(
    db: Session,
    *,
    email_attempted: str,
    user: User | None,
    success: bool,
    auth_method: str,
    failure_reason: str | None = None,
    request: Request | None = None,
) -> LoginHistory:
    row = LoginHistory(
        user_id=getattr(user, "id", None),
        school_id=getattr(user, "school_id", None),
        email_attempted=email_attempted.strip().lower(),
        success=success,
        auth_method=auth_method,
        failure_reason=failure_reason,
        ip_address=_request_ip(request),
        user_agent=_request_agent(request),
    )
    db.add(row)
    db.flush()
    return row


def create_user_session(
    db: Session,
    *,
    user: User,
    token_jti: str,
    session_id: str,
    expires_in_minutes: int,
    request: Request | None = None,
) -> UserSession:
    now = utc_now()
    session = UserSession(
        id=uuid.UUID(session_id),
        user_id=user.id,
        token_jti=token_jti,
        ip_address=_request_ip(request),
        user_agent=_request_agent(request),
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(minutes=max(1, expires_in_minutes)),
    )
    db.add(session)
    db.flush()
    return session


def assert_session_valid(
    db: Session,
    *,
    token_jti: Optional[str],
) -> Optional[UserSession]:
    if not token_jti:
        return None
    session = db.query(UserSession).filter(UserSession.token_jti == token_jti).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is not valid")
    if session.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been revoked")
    expires_at = ensure_utc(session.expires_at)
    now = utc_now()
    if expires_at is not None and expires_at < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has expired")
    return session


def revoke_session(
    db: Session,
    *,
    session_id: str,
    actor_user_id: int,
    allow_self: bool = True,
) -> bool:
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session is None:
        return False
    if session.user_id != actor_user_id and not allow_self:
        return False
    if session.revoked_at is None:
        session.revoked_at = utc_now()
        db.flush()
    return True


def revoke_other_sessions(db: Session, *, actor_user_id: int, current_session_id: str | None) -> int:
    query = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == actor_user_id,
            UserSession.revoked_at.is_(None),
        )
    )
    if current_session_id:
        query = query.filter(UserSession.id != current_session_id)
    sessions = query.all()
    now = utc_now()
    for session in sessions:
        session.revoked_at = now
    db.flush()
    return len(sessions)


def list_active_sessions(
    db: Session,
    *,
    actor_user_id: int,
) -> list[UserSession]:
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == actor_user_id)
        .order_by(UserSession.created_at.desc())
        .limit(100)
        .all()
    )


def list_login_history_for_actor(
    db: Session,
    *,
    actor: User,
    limit: int,
) -> list[LoginHistory]:
    role_names = _normalize_role_names(actor)
    effective_limit = max(1, min(limit, 500))

    query = db.query(LoginHistory).order_by(LoginHistory.created_at.desc())
    is_platform_admin = "admin" in role_names and getattr(actor, "school_id", None) is None

    if is_platform_admin:
        return query.limit(effective_limit).all()

    if "admin" in role_names or "campus-admin" in role_names:
        school_id = getattr(actor, "school_id", None)
        if school_id is None:
            return []
        return query.filter(LoginHistory.school_id == school_id).limit(effective_limit).all()

    return (
        query.filter(LoginHistory.user_id == actor.id)
        .limit(effective_limit)
        .all()
    )

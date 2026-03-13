from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import secrets
import uuid
from typing import Iterable, Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.platform_features import LoginHistory, MfaChallenge, UserSecuritySetting, UserSession
from app.models.user import User


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
        role_key = role_name.strip().lower().replace("_", "-")
        if role_key:
            normalized.add(role_key)
    return normalized


def is_privileged_user(user: User) -> bool:
    role_names = _normalize_role_names(user)
    return "admin" in role_names or "school-it" in role_names


def get_or_create_security_setting(db: Session, user: User) -> UserSecuritySetting:
    setting = db.query(UserSecuritySetting).filter(UserSecuritySetting.user_id == user.id).first()
    if setting:
        return setting

    setting = UserSecuritySetting(
        user_id=user.id,
        mfa_enabled=is_privileged_user(user),
        trusted_device_days=14,
    )
    db.add(setting)
    db.flush()
    return setting


def should_require_mfa(db: Session, user: User) -> bool:
    settings = get_settings()
    if not settings.auth_enable_mfa:
        return False

    setting = get_or_create_security_setting(db, user)
    return bool(setting.mfa_enabled)


def _mfa_code_hash(challenge_id: str, code: str) -> str:
    payload = f"{challenge_id}:{code.strip()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_mfa_challenge(
    db: Session,
    *,
    user: User,
    request: Optional[Request] = None,
    ttl_minutes: int = 10,
) -> tuple[MfaChallenge, str]:
    challenge_id = str(uuid.uuid4())
    code = "".join(str(secrets.randbelow(10)) for _ in range(6))
    challenge = MfaChallenge(
        id=challenge_id,
        user_id=user.id,
        code_hash=_mfa_code_hash(challenge_id, code),
        channel="email",
        attempts=0,
        expires_at=datetime.utcnow() + timedelta(minutes=max(1, ttl_minutes)),
        ip_address=_request_ip(request),
        user_agent=_request_agent(request),
    )
    db.add(challenge)
    db.flush()
    return challenge, code


def verify_mfa_challenge(
    db: Session,
    *,
    user: User,
    challenge_id: str,
    code: str,
    max_attempts: int = 5,
) -> MfaChallenge:
    challenge = (
        db.query(MfaChallenge)
        .filter(
            MfaChallenge.id == challenge_id,
            MfaChallenge.user_id == user.id,
        )
        .first()
    )
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MFA challenge not found")

    if challenge.consumed_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA challenge already used")
    if challenge.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA challenge expired")
    if challenge.attempts >= max_attempts:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="MFA attempts exceeded")

    submitted_hash = _mfa_code_hash(challenge_id, code)
    if submitted_hash != challenge.code_hash:
        challenge.attempts += 1
        db.flush()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

    challenge.consumed_at = datetime.utcnow()
    db.flush()
    return challenge


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
    now = datetime.utcnow()
    session = UserSession(
        id=session_id,
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
    if session.expires_at < datetime.utcnow():
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
        session.revoked_at = datetime.utcnow()
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
    now = datetime.utcnow()
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

    if "admin" in role_names or "school-it" in role_names:
        school_id = getattr(actor, "school_id", None)
        if school_id is None:
            return []
        return query.filter(LoginHistory.school_id == school_id).limit(effective_limit).all()

    return (
        query.filter(LoginHistory.user_id == actor.id)
        .limit(effective_limit)
        .all()
    )

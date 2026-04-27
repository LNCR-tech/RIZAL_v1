"""Use: Contains the main backend rules for login session building and account-state checks.
Where to use: Use this from routers, workers, or other services when login session building and account-state checks logic is needed.
Role: Service layer. It keeps business logic out of the route files.
"""

from __future__ import annotations

from datetime import timedelta
import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    canonicalize_role_name_for_storage,
    create_access_token,
    validate_user_account_state,
)
from app.models.face_recognition import UserFaceRecognitionProfile
from app.models.school import School, SchoolSetting
from app.models.user import User
from app.services import governance_hierarchy_service
from app.services.security_service import create_user_session
from app.services.user_preference_service import get_or_create_user_security_setting
from app.services.face_recognition import is_face_scan_bypass_enabled_for_user

BASE_AUTH_ROLE_NAMES = {"admin", "campus_admin", "student"}
PRIVILEGED_AUTH_ROLE_NAMES = {"admin", "campus_admin"}


def get_user_role_names(user: User) -> list[str]:
    role_names = []
    seen = set()
    for role_assignment in getattr(user, "roles", []):
        role = getattr(role_assignment, "role", None)
        role_name = getattr(role, "name", None)
        if not role_name:
            continue
        canonical_name = canonicalize_role_name_for_storage(role_name)
        if canonical_name not in BASE_AUTH_ROLE_NAMES or canonical_name in seen:
            continue
        seen.add(canonical_name)
        role_names.append(canonical_name)
    return role_names


def validate_login_account_state(db: Session, user: User) -> None:
    validate_user_account_state(db, user)


def _get_governance_role_names(db: Session, user: User) -> list[str]:
    """Expose governance memberships as assistant-friendly role strings (ssg/sg/org)."""
    if getattr(user, "school_id", None) is None:
        return []
    try:
        unit_types = governance_hierarchy_service.get_user_governance_unit_types(
            db,
            current_user=user,
        )
    except Exception:
        return []

    # GovernanceUnitType values are "SSG"/"SG"/"ORG".
    role_names: list[str] = []
    for unit_type in sorted({ut.value for ut in unit_types}):
        normalized = str(unit_type).strip().lower()
        if normalized in {"ssg", "sg", "org"}:
            role_names.append(normalized)
    return role_names


def _get_governance_permission_codes(db: Session, user: User) -> list[str]:
    """Expose governance member permission codes for assistant MCP policy enforcement."""
    if getattr(user, "school_id", None) is None:
        return []
    try:
        permission_codes = governance_hierarchy_service.get_user_governance_permission_codes(
            db,
            current_user=user,
        )
    except Exception:
        return []
    return sorted({str(code.value).strip().lower() for code in permission_codes if getattr(code, "value", None)})


def get_school_context(db: Session, user: User) -> dict[str, object | None]:
    try:
        school_id = getattr(user, "school_id", None)
        if school_id is None:
            return {}

        school = getattr(user, "school", None)
        if school is None:
            school = db.query(School).filter(School.id == school_id).first()
        if school is None:
            return {}

        settings = getattr(school, "settings", None)
        if settings is None:
            settings = (
                db.query(SchoolSetting)
                .filter(SchoolSetting.school_id == school.id)
                .first()
            )

        return {
            "school_id": school.id,
            "school_name": school.school_name or school.name,
            "school_code": school.school_code,
            "logo_url": school.logo_url,
            "primary_color": school.primary_color
            if getattr(school, "primary_color", None)
            else (settings.primary_color if settings else None),
            "secondary_color": school.secondary_color
            if getattr(school, "secondary_color", None)
            else (settings.secondary_color if settings else None),
            "accent_color": settings.accent_color
            if settings
            else (school.secondary_color or school.primary_color),
        }
    except Exception:
        return {}


def has_face_reference_enrolled(db: Session, user_id: int) -> bool:
    # user_face_profiles table has been dropped — face enrollment is now
    # tracked via student_face_embeddings. Always return False here;
    # the caller also checks getattr(user, 'face_profile', None) which
    # covers the new path.
    return False


def should_recommend_password_change(user: User) -> bool:
    return bool(
        getattr(user, "should_prompt_password_change", False)
        and not getattr(user, "must_change_password", False)
    )


def _resolve_session_duration_minutes(
    *,
    db: Session,
    user: User,
    remember_me: bool,
) -> int:
    if not remember_me:
        return ACCESS_TOKEN_EXPIRE_MINUTES

    security_setting = get_or_create_user_security_setting(db, user=user)
    trusted_device_days = max(1, int(security_setting.trusted_device_days or 14))
    return trusted_device_days * 24 * 60


def _should_require_face_scan_mfa(db: Session, user: User, role_names: list[str]) -> bool:
    if not get_settings().privileged_face_verification_enabled:
        return False
    if is_face_scan_bypass_enabled_for_user(user):
        return False
    if not any(role_name in PRIVILEGED_AUTH_ROLE_NAMES for role_name in role_names):
        return False

    security_setting = get_or_create_user_security_setting(db, user=user)
    return bool(security_setting.mfa_enabled)


def issue_full_access_token_response(
    *,
    db: Session,
    user: User,
    request: Request | None = None,
    expires_minutes: int | None = None,
) -> dict[str, object | None]:
    base_roles = get_user_role_names(user)
    governance_roles = _get_governance_role_names(db, user)
    permission_codes = _get_governance_permission_codes(db, user)
    role_names = [*base_roles]
    for role_name in governance_roles:
        if role_name not in role_names:
            role_names.append(role_name)
    school_context = get_school_context(db, user)
    face_reference_enrolled = (
        getattr(user, "face_profile", None) is not None
        or has_face_reference_enrolled(db, user.id)
    )
    resolved_expires_minutes = max(1, int(expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES))
    session_id = str(uuid.uuid4())
    token_jti = str(uuid.uuid4())

    token_payload = {
        "sub": user.email,
        "roles": role_names,
        "permissions": permission_codes,
        "user_id": user.id,
        "is_admin": "admin" in role_names,
        "must_change_password": user.must_change_password,
        "jti": token_jti,
        "sid": session_id,
        "face_pending": False,
        "session_duration_minutes": resolved_expires_minutes,
    }
    if school_context.get("school_id") is not None:
        token_payload["school_id"] = school_context["school_id"]

    access_token = create_access_token(
        data=token_payload,
        expires_delta=timedelta(minutes=resolved_expires_minutes),
    )
    create_user_session(
        db,
        user=user,
        token_jti=token_jti,
        session_id=session_id,
        expires_in_minutes=resolved_expires_minutes,
        request=request,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user.email,
        "roles": role_names,
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_admin": "admin" in role_names,
        "must_change_password": user.must_change_password,
        "password_change_recommended": should_recommend_password_change(user),
        "session_id": session_id,
        "face_verification_required": False,
        "face_reference_enrolled": face_reference_enrolled,
        "face_verification_pending": False,
        **school_context,
    }


def issue_face_pending_token_response(
    *,
    db: Session,
    user: User,
    expires_minutes: int,
) -> dict[str, object | None]:
    role_names = get_user_role_names(user)
    school_context = get_school_context(db, user)
    face_reference_enrolled = (
        getattr(user, "face_profile", None) is not None
        or has_face_reference_enrolled(db, user.id)
    )
    resolved_expires_minutes = max(1, int(expires_minutes))

    token_payload = {
        "sub": user.email,
        "roles": role_names,
        "user_id": user.id,
        "is_admin": "admin" in role_names,
        "must_change_password": user.must_change_password,
        "face_pending": True,
        "session_duration_minutes": resolved_expires_minutes,
    }
    if school_context.get("school_id") is not None:
        token_payload["school_id"] = school_context["school_id"]

    access_token = create_access_token(
        data=token_payload,
        expires_delta=timedelta(minutes=resolved_expires_minutes),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user.email,
        "roles": role_names,
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_admin": "admin" in role_names,
        "must_change_password": user.must_change_password,
        "password_change_recommended": should_recommend_password_change(user),
        "session_id": None,
        "face_verification_required": True,
        "face_reference_enrolled": face_reference_enrolled,
        "face_verification_pending": True,
        **school_context,
    }


def issue_login_token_response(
    *,
    db: Session,
    user: User,
    request: Request | None = None,
    remember_me: bool = False,
) -> dict[str, object | None]:
    validate_login_account_state(db, user)
    role_names = get_user_role_names(user)
    expires_minutes = _resolve_session_duration_minutes(
        db=db,
        user=user,
        remember_me=remember_me,
    )

    if _should_require_face_scan_mfa(db, user, role_names):
        return issue_face_pending_token_response(
            db=db,
            user=user,
            expires_minutes=expires_minutes,
        )

    return issue_full_access_token_response(
        db=db,
        user=user,
        request=request,
        expires_minutes=expires_minutes,
    )

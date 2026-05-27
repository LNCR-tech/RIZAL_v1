"""Use: Handles login and authentication API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs login and authentication features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

import hashlib
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.timezones import utc_now
from app.core.rate_limit import (
    build_forgot_password_rule,
    build_login_rule,
    client_ip_identity,
    enforce_rate_limit,
)
from app.core.security import (
    PASSWORD_CHANGE_PROMPT_DISMISS_ENDPOINT,
    authenticate_user,
    get_current_admin_or_campus_admin,
    get_current_application_user,
    has_any_role,
    verify_password,
)
from app.core.dependencies import get_db
from app.schemas.auth import ChangePasswordRequest, Token, LoginRequest
from app.schemas.google_auth import GoogleLoginRequest
from app.services.google_auth_service import (
    GoogleAuthDisabledError,
    GoogleAuthInvalidTokenError,
    GoogleEmailNotVerifiedError,
    verify_google_access_token,
    verify_google_id_token,
)
from app.schemas.common import MessageResponse
from app.schemas.password_reset import (
    ForgotPasswordRequestCreate,
    ForgotPasswordRequestResponse,
    PasswordResetCodeResponse,
    ResetPasswordRequest,
    VerifyResetCodeRequest,
    VerifyResetCodeResponse,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.school import School
from app.models.user import User, UserRole
from app.services.email_service import (
    EmailDeliveryError,
    send_password_reset_code_email,
)
from app.services.auth_session import (
    issue_login_token_response,
    validate_login_account_state,
)
from app.services.notification_center_service import send_account_security_notification
from app.services.password_change_policy import must_change_password_for_temporary_reset
from app.services.security_service import (
    record_login_history,
)

router = APIRouter(tags=["authentication"])
FORGOT_PASSWORD_GENERIC_MESSAGE = (
    "If an account with that email exists, a reset code has been sent."
)
RESET_CODE_EXPIRY_MINUTES = 15


def _is_platform_admin_account(user: User | None) -> bool:
    return bool(user) and has_any_role(user, ["admin"]) and getattr(user, "school_id", None) is None


def _can_submit_public_password_reset_request(user: User | None) -> bool:
    if user is None or not getattr(user, "is_active", True):
        return False
    if getattr(user, "school_id", None) is None:
        return False
    return not _is_platform_admin_account(user)


def _login_rate_limit_identity(request: Request, email: str) -> str:
    return f"{client_ip_identity(request)}:email:{email.strip().lower()}"


def _try_commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()


def _try_record_login_history(db: Session, **kwargs) -> None:
    try:
        record_login_history(db, **kwargs)
    except Exception:
        db.rollback()


@router.post("/token", response_model=Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: bool = Form(default=False),
    db: Session = Depends(get_db)
):
    """OAuth2-compatible token endpoint (for Swagger UI)"""
    enforce_rate_limit(
        build_login_rule(),
        _login_rate_limit_identity(request, form_data.username),
        request=request,
    )
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        _try_record_login_history(
            db,
            email_attempted=form_data.username,
            user=None,
            success=False,
            auth_method="password",
            failure_reason="invalid_credentials",
            request=request,
        )
        _try_commit(db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    validate_login_account_state(db, user)

    response_payload = issue_login_token_response(
        db=db,
        user=user,
        request=request,
        remember_me=remember_me,
    )
    _try_record_login_history(
        db,
        email_attempted=user.email,
        user=user,
        success=True,
        auth_method="password",
        request=request,
    )
    _try_commit(db)
    return response_payload

@router.post("/login", response_model=Token)
def login_with_email(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Alternative login endpoint that returns extended user info"""
    enforce_rate_limit(
        build_login_rule(),
        _login_rate_limit_identity(request, login_data.email),
        request=request,
    )
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        _try_record_login_history(
            db,
            email_attempted=login_data.email,
            user=None,
            success=False,
            auth_method="password",
            failure_reason="invalid_credentials",
            request=request,
        )
        _try_commit(db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    validate_login_account_state(db, user)

    response_payload = issue_login_token_response(
        db=db,
        user=user,
        request=request,
        remember_me=login_data.remember_me,
        platform=login_data.platform,
    )
    _try_record_login_history(
        db,
        email_attempted=user.email,
        user=user,
        success=True,
        auth_method="password",
        request=request,
    )

    _try_commit(db)
    return response_payload


@router.post("/auth/google", response_model=Token)
def login_with_google(
    request: Request,
    payload: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    """Verify a Google ID token and issue an access token for a registered user."""
    enforce_rate_limit(
        build_login_rule(),
        f"{client_ip_identity(request)}:google",
        request=request,
    )

    try:
        if payload.id_token:
            google_payload = verify_google_id_token(payload.id_token)
        else:
            google_payload = verify_google_access_token(payload.access_token)
    except GoogleAuthDisabledError:
        record_login_history(
            db,
            email_attempted="",
            user=None,
            success=False,
            auth_method="google",
            failure_reason="google_login_disabled",
            request=request,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Google login is disabled.")
    except GoogleEmailNotVerifiedError:
        record_login_history(
            db,
            email_attempted="",
            user=None,
            success=False,
            auth_method="google",
            failure_reason="email_not_verified",
            request=request,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google email is not verified.")
    except GoogleAuthInvalidTokenError:
        record_login_history(
            db,
            email_attempted="",
            user=None,
            success=False,
            auth_method="google",
            failure_reason="invalid_token",
            request=request,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token.")

    email = google_payload["email"]

    user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(UserRole.role))
        .filter(User.email == email)
        .first()
    )
    if user is None:
        record_login_history(
            db,
            email_attempted=email,
            user=None,
            success=False,
            auth_method="google",
            failure_reason="not_registered",
            request=request,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Google account is not registered.")

    validate_login_account_state(db, user)

    response_payload = issue_login_token_response(
        db=db,
        user=user,
        request=request,
        remember_me=False,
    )
    record_login_history(
        db,
        email_attempted=user.email,
        user=user,
        success=True,
        auth_method="google",
        request=request,
    )
    db.commit()
    return response_payload


@router.post("/auth/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    # Use the same verifier as login so temporary passwords work consistently
    # regardless of which hashing helper originally created the stored hash.
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.set_password(payload.new_password)
    current_user.must_change_password = False
    current_user.should_prompt_password_change = False
    try:
        send_account_security_notification(
            db,
            user=current_user,
            subject="Password Changed",
            message="Your password was changed successfully.",
            metadata_json={"event": "password_change"},
        )
    except Exception:
        pass
    db.commit()

    return {"message": "Password updated successfully"}


@router.post(PASSWORD_CHANGE_PROMPT_DISMISS_ENDPOINT, response_model=MessageResponse)
def dismiss_password_change_prompt(
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    current_user.should_prompt_password_change = False
    db.commit()
    return {"message": "Password change prompt dismissed."}


@router.post("/auth/forgot-password", response_model=ForgotPasswordRequestResponse)
def request_forgot_password(
    request: Request,
    payload: ForgotPasswordRequestCreate,
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()
    enforce_rate_limit(
        build_forgot_password_rule(),
        _login_rate_limit_identity(request, normalized_email),
        request=request,
    )
    target_user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(UserRole.role))
        .filter(User.email == normalized_email)
        .first()
    )

    if not target_user or not _can_submit_public_password_reset_request(target_user):
        return ForgotPasswordRequestResponse(message=FORGOT_PASSWORD_GENERIC_MESSAGE)

    code = f"{secrets.randbelow(1_000_000):06d}"
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    expires_at = utc_now() + timedelta(minutes=RESET_CODE_EXPIRY_MINUTES)

    db.add(
        PasswordResetToken(
            user_id=target_user.id,
            code_hash=code_hash,
            expires_at=expires_at,
        )
    )

    school = db.query(School).filter(School.id == target_user.school_id).first()
    system_name = (school.school_name or school.name) if school else None

    try:
        send_password_reset_code_email(
            recipient_email=target_user.email,
            code=code,
            first_name=target_user.first_name,
            system_name=system_name,
        )
    except EmailDeliveryError:
        db.rollback()
        return ForgotPasswordRequestResponse(message=FORGOT_PASSWORD_GENERIC_MESSAGE)

    db.commit()
    return ForgotPasswordRequestResponse(message=FORGOT_PASSWORD_GENERIC_MESSAGE)


@router.post("/auth/verify-reset-code", response_model=VerifyResetCodeResponse)
def verify_reset_code(
    request: Request,
    payload: VerifyResetCodeRequest,
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()
    enforce_rate_limit(
        build_forgot_password_rule(),
        _login_rate_limit_identity(request, normalized_email),
        request=request,
    )

    target_user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(UserRole.role))
        .filter(User.email == normalized_email)
        .first()
    )

    if not target_user or not _can_submit_public_password_reset_request(target_user):
        raise HTTPException(status_code=400, detail="Invalid or expired reset code.")

    submitted_hash = hashlib.sha256(payload.code.strip().encode()).hexdigest()
    now = utc_now()

    token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == target_user.id,
            PasswordResetToken.code_hash == submitted_hash,
            PasswordResetToken.expires_at > now,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.reset_token.is_(None),
        )
        .first()
    )

    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code.")

    reset_token = secrets.token_urlsafe(32)
    token.reset_token = reset_token
    db.commit()

    return VerifyResetCodeResponse(reset_token=reset_token)


@router.post("/auth/reset-password", response_model=PasswordResetCodeResponse)
def reset_password_with_token(
    request: Request,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    now = utc_now()

    token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.reset_token == payload.reset_token,
            PasswordResetToken.expires_at > now,
            PasswordResetToken.used_at.is_(None),
        )
        .first()
    )

    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    target_user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(UserRole.role))
        .filter(User.id == token.user_id)
        .first()
    )

    if not target_user or not _can_submit_public_password_reset_request(target_user):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    token.used_at = now
    target_user.set_password(payload.new_password)
    target_user.must_change_password = False
    target_user.should_prompt_password_change = False

    try:
        send_account_security_notification(
            db,
            user=target_user,
            subject="Password Reset",
            message="Your password was reset using a self-service reset code.",
            metadata_json={"event": "password_reset_code"},
        )
    except Exception:
        pass

    db.commit()
    return PasswordResetCodeResponse(message="Password has been reset successfully.")



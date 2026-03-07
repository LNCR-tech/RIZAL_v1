from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.security import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user_with_roles,
    has_any_role,
)
from app.database import get_db
from app.schemas.auth import ChangePasswordRequest, Token, LoginRequest
from app.schemas.security import MfaChallengeVerifyRequest
from app.schemas.password_reset import (
    ForgotPasswordRequestCreate,
    ForgotPasswordRequestResponse,
    PasswordResetApprovalResponse,
    PasswordResetRequestItem,
)
from app.models.password_reset_request import PasswordResetRequest
from app.models.user import User, UserRole
from app.models.school import School, SchoolSetting
from app.services.email_service import EmailDeliveryError, send_mfa_code_email, send_password_reset_email
from app.services.notification_center_service import send_account_security_notification
from app.services.security_service import (
    create_mfa_challenge,
    create_user_session,
    record_login_history,
    should_require_mfa,
    verify_mfa_challenge,
)
from app.utils.passwords import generate_secure_password

router = APIRouter(tags=["authentication"])
PASSWORD_CHANGE_ENDPOINT = "/auth/change-password"
FORGOT_PASSWORD_GENERIC_MESSAGE = (
    "If the account exists, a password reset request has been submitted for School IT approval."
)


def _get_school_context(db: Session, user: User) -> dict:
    """
    Resolve school context strictly from the authenticated user's school_id.
    Do not fall back to any other school to avoid cross-tenant data leakage.
    """
    try:
        school_id = getattr(user, "school_id", None)
        if school_id is None:
            return {}
        school = db.query(School).filter(School.id == school_id).first()
        if school is None:
            return {}

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
            "primary_color": school.primary_color if getattr(school, "primary_color", None) else (settings.primary_color if settings else None),
            "secondary_color": school.secondary_color if getattr(school, "secondary_color", None) else (settings.secondary_color if settings else None),
            "accent_color": settings.accent_color if settings else (school.secondary_color or school.primary_color),
        }
    except Exception:
        # Avoid breaking authentication if school tables are not migrated yet.
        return {}


def _issue_access_token_response(
    *,
    db: Session,
    user: User,
    role_names: list[str],
    school_context: dict,
    request: Request | None = None,
) -> dict:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    session_id = str(uuid.uuid4())
    token_jti = str(uuid.uuid4())

    token_payload = {
        "sub": user.email,
        "roles": role_names,
        "user_id": user.id,
        "is_admin": "admin" in role_names,
        "must_change_password": user.must_change_password,
        "jti": token_jti,
        "sid": session_id,
    }
    if school_context.get("school_id") is not None:
        token_payload["school_id"] = school_context["school_id"]

    access_token = create_access_token(
        data=token_payload,
        expires_delta=access_token_expires,
    )
    create_user_session(
        db,
        user=user,
        token_jti=token_jti,
        session_id=session_id,
        expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
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
        "change_password_endpoint": PASSWORD_CHANGE_ENDPOINT if user.must_change_password else None,
        "session_id": session_id,
        **school_context,
    }

@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2-compatible token endpoint (for Swagger UI)"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        record_login_history(
            db,
            email_attempted=form_data.username,
            user=None,
            success=False,
            auth_method="password",
            failure_reason="invalid_credentials",
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_names = [ur.role.name for ur in user.roles]
    school_context = _get_school_context(db, user)
    response_payload = _issue_access_token_response(
        db=db,
        user=user,
        role_names=role_names,
        school_context=school_context,
        request=request,
    )
    record_login_history(
        db,
        email_attempted=user.email,
        user=user,
        success=True,
        auth_method="password",
        request=request,
    )
    db.commit()
    return response_payload

@router.post("/login", response_model=Token)
async def login_with_email(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Alternative login endpoint that returns extended user info"""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        record_login_history(
            db,
            email_attempted=login_data.email,
            user=None,
            success=False,
            auth_method="password",
            failure_reason="invalid_credentials",
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    role_names = [ur.role.name for ur in user.roles]
    school_context = _get_school_context(db, user)

    if should_require_mfa(db, user):
        challenge, code = create_mfa_challenge(db, user=user, request=request, ttl_minutes=10)
        try:
            send_mfa_code_email(
                recipient_email=user.email,
                code=code,
                first_name=user.first_name,
                system_name=school_context.get("school_name"),
            )
        except EmailDeliveryError as exc:
            db.rollback()
            raise HTTPException(status_code=502, detail=f"Failed to send MFA code: {exc}") from exc

        record_login_history(
            db,
            email_attempted=user.email,
            user=user,
            success=True,
            auth_method="password_mfa_pending",
            request=request,
        )
        db.commit()
        return {
            "access_token": None,
            "token_type": "mfa",
            "email": user.email,
            "roles": role_names,
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_admin": "admin" in role_names,
            "must_change_password": user.must_change_password,
            "mfa_required": True,
            "mfa_challenge_id": challenge.id,
            "mfa_expires_at": challenge.expires_at,
            **school_context,
        }

    response_payload = _issue_access_token_response(
        db=db,
        user=user,
        role_names=role_names,
        school_context=school_context,
        request=request,
    )
    record_login_history(
        db,
        email_attempted=user.email,
        user=user,
        success=True,
        auth_method="password",
        request=request,
    )

    try:
        send_account_security_notification(
            db,
            user=user,
            subject="New Login Detected",
            message=(
                "A new login to your VALID8 account was detected. "
                "If this wasn't you, reset your password immediately."
            ),
            metadata_json={"event": "login"},
        )
    except Exception:
        # Authentication should succeed even if notifications fail.
        pass

    db.commit()
    return response_payload


@router.post("/auth/mfa/verify", response_model=Token)
async def verify_mfa_and_login(
    request: Request,
    payload: MfaChallengeVerifyRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(UserRole.role))
        .filter(User.email == payload.email.strip().lower())
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    challenge = verify_mfa_challenge(
        db,
        user=user,
        challenge_id=payload.challenge_id,
        code=payload.code,
    )
    role_names = [ur.role.name for ur in user.roles]
    school_context = _get_school_context(db, user)
    response_payload = _issue_access_token_response(
        db=db,
        user=user,
        role_names=role_names,
        school_context=school_context,
        request=request,
    )
    record_login_history(
        db,
        email_attempted=user.email,
        user=user,
        success=True,
        auth_method="mfa",
        request=request,
    )
    try:
        send_account_security_notification(
            db,
            user=user,
            subject="MFA Login Completed",
            message=(
                "A multi-factor login was completed successfully on your VALID8 account."
            ),
            metadata_json={"event": "mfa_login", "challenge_id": challenge.id},
        )
    except Exception:
        pass
    db.commit()
    return response_payload


@router.post("/auth/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    if not current_user.check_password(payload.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.set_password(payload.new_password)
    current_user.must_change_password = False
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


@router.post("/auth/forgot-password", response_model=ForgotPasswordRequestResponse)
async def request_forgot_password(
    payload: ForgotPasswordRequestCreate,
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()
    target_user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(UserRole.role))
        .filter(User.email == normalized_email)
        .first()
    )

    if not target_user:
        return ForgotPasswordRequestResponse(message=FORGOT_PASSWORD_GENERIC_MESSAGE)

    if not getattr(target_user, "is_active", True) or getattr(target_user, "school_id", None) is None:
        return ForgotPasswordRequestResponse(message=FORGOT_PASSWORD_GENERIC_MESSAGE)

    if has_any_role(target_user, ["admin", "school_IT", "school-it", "school_it"]):
        return ForgotPasswordRequestResponse(message=FORGOT_PASSWORD_GENERIC_MESSAGE)

    existing_pending = (
        db.query(PasswordResetRequest)
        .filter(
            PasswordResetRequest.user_id == target_user.id,
            PasswordResetRequest.status == "pending",
        )
        .first()
    )
    if existing_pending:
        return ForgotPasswordRequestResponse(message=FORGOT_PASSWORD_GENERIC_MESSAGE)

    db.add(
        PasswordResetRequest(
            user_id=target_user.id,
            school_id=target_user.school_id,
            requested_email=target_user.email.lower(),
            status="pending",
        )
    )
    db.commit()

    return ForgotPasswordRequestResponse(message=FORGOT_PASSWORD_GENERIC_MESSAGE)


@router.get("/auth/password-reset-requests", response_model=list[PasswordResetRequestItem])
async def list_password_reset_requests(
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    if not has_any_role(current_user, ["school_IT", "admin"]):
        raise HTTPException(status_code=403, detail="School IT or admin role required")

    is_platform_admin = has_any_role(current_user, ["admin"]) and getattr(current_user, "school_id", None) is None

    query = (
        db.query(PasswordResetRequest)
        .options(joinedload(PasswordResetRequest.user).joinedload(User.roles).joinedload(UserRole.role))
        .filter(PasswordResetRequest.status == "pending")
        .order_by(PasswordResetRequest.requested_at.asc())
    )

    if not is_platform_admin:
        actor_school_id = getattr(current_user, "school_id", None)
        if actor_school_id is None:
            raise HTTPException(status_code=403, detail="User is not assigned to a school")
        query = query.filter(PasswordResetRequest.school_id == actor_school_id)

    requests = query.all()
    return [
        PasswordResetRequestItem(
            id=item.id,
            user_id=item.user.id,
            email=item.user.email,
            first_name=item.user.first_name,
            last_name=item.user.last_name,
            roles=[role.role.name for role in item.user.roles if getattr(role, "role", None)],
            status=item.status,
            requested_at=item.requested_at,
        )
        for item in requests
        if item.user is not None
    ]


@router.post("/auth/password-reset-requests/{request_id}/approve", response_model=PasswordResetApprovalResponse)
async def approve_password_reset_request(
    request_id: int,
    current_user: User = Depends(get_current_user_with_roles),
    db: Session = Depends(get_db),
):
    if not has_any_role(current_user, ["school_IT", "admin"]):
        raise HTTPException(status_code=403, detail="School IT or admin role required")

    request_item = (
        db.query(PasswordResetRequest)
        .options(joinedload(PasswordResetRequest.user).joinedload(User.roles).joinedload(UserRole.role))
        .filter(
            PasswordResetRequest.id == request_id,
            PasswordResetRequest.status == "pending",
        )
        .first()
    )

    if not request_item or not request_item.user:
        raise HTTPException(status_code=404, detail="Pending password reset request not found")

    is_platform_admin = has_any_role(current_user, ["admin"]) and getattr(current_user, "school_id", None) is None
    if not is_platform_admin:
        actor_school_id = getattr(current_user, "school_id", None)
        if actor_school_id is None or actor_school_id != request_item.school_id:
            raise HTTPException(status_code=404, detail="Password reset request not found")

    target_user = request_item.user
    if not getattr(target_user, "is_active", True):
        raise HTTPException(status_code=400, detail="Target user is inactive")

    if has_any_role(current_user, ["school_IT"]) and not has_any_role(current_user, ["admin"]):
        if has_any_role(target_user, ["admin", "school_IT", "school-it", "school_it"]):
            raise HTTPException(
                status_code=403,
                detail="SCHOOL_IT cannot reset admin or SCHOOL_IT accounts.",
            )
        if current_user.id == target_user.id:
            raise HTTPException(status_code=403, detail="SCHOOL_IT cannot approve their own reset request.")

    temporary_password = generate_secure_password(min_length=10, max_length=14)
    target_user.set_password(temporary_password)
    target_user.must_change_password = True

    request_item.status = "approved"
    request_item.resolved_at = datetime.utcnow()
    request_item.reviewed_by_user_id = current_user.id

    school = db.query(School).filter(School.id == request_item.school_id).first()
    system_name = (school.school_name or school.name) if school else None

    try:
        send_password_reset_email(
            recipient_email=target_user.email,
            temporary_password=temporary_password,
            first_name=target_user.first_name,
            system_name=system_name,
        )
        try:
            send_account_security_notification(
                db,
                user=target_user,
                subject="Password Reset Approved",
                message="Your password reset request was approved. Use your temporary password to log in.",
                metadata_json={"event": "password_reset_approved", "request_id": request_item.id},
            )
        except Exception:
            pass
    except EmailDeliveryError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Failed to send password reset email: {exc}") from exc

    db.commit()

    return PasswordResetApprovalResponse(
        id=request_item.id,
        user_id=target_user.id,
        status=request_item.status,
        resolved_at=request_item.resolved_at or datetime.utcnow(),
        message="Password reset approved and temporary password emailed.",
    )

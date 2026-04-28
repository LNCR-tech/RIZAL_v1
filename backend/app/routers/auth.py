"""Use: Handles login and authentication API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs login and authentication features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

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
    verify_user_password,
)
from app.core.dependencies import get_db
from app.schemas.auth import ChangePasswordRequest, Token, LoginRequest
from app.schemas.common import MessageResponse
from app.schemas.password_reset import (
    ForgotPasswordRequestCreate,
    ForgotPasswordRequestResponse,
    PasswordResetApprovalResponse,
    PasswordResetRequestItem,
)
from app.models.password_reset_request import PasswordResetRequest
from app.models.user import User, UserRole
from app.services.auth_session import (
    issue_login_token_response,
    validate_login_account_state,
)
from app.services.notification_center_service import send_account_security_notification
from app.services.password_change_policy import (
    must_change_password_for_new_account,
    must_change_password_for_temporary_reset,
    should_prompt_password_change_for_new_account,
)
from app.services.security_service import (
    record_login_history,
)
from app.utils.passwords import generate_secure_password, hash_student_default_password

router = APIRouter(tags=["authentication"])
FORGOT_PASSWORD_GENERIC_MESSAGE = (
    "If an eligible student account exists, its password has been reset to the default password."
)


def _is_platform_admin_account(user: User | None) -> bool:
    return bool(user) and has_any_role(user, ["admin"]) and getattr(user, "school_id", None) is None


def _requires_platform_admin_password_reset_approval(user: User | None) -> bool:
    return bool(user) and has_any_role(user, ["admin", "campus_admin"])


def _can_submit_public_password_reset_request(user: User | None) -> bool:
    if user is None or not getattr(user, "is_active", True):
        return False
    if getattr(user, "school_id", None) is None:
        return False
    return not _is_platform_admin_account(user)


def _can_auto_reset_student_default_password(user: User | None) -> bool:
    if not _can_submit_public_password_reset_request(user):
        return False
    if _requires_platform_admin_password_reset_approval(user):
        return False
    return has_any_role(user, ["student"])


def _login_rate_limit_identity(request: Request, email: str) -> str:
    return f"{client_ip_identity(request)}:email:{email.strip().lower()}"

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
    validate_login_account_state(db, user)

    response_payload = issue_login_token_response(
        db=db,
        user=user,
        request=request,
        remember_me=remember_me,
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
    validate_login_account_state(db, user)

    response_payload = issue_login_token_response(
        db=db,
        user=user,
        request=request,
        remember_me=login_data.remember_me,
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


@router.post("/auth/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    # Use the same verifier as login so temporary passwords work consistently
    # regardless of which hashing helper originally created the stored hash.
    if not verify_user_password(current_user, payload.current_password):
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

    if not _can_auto_reset_student_default_password(target_user):
        return ForgotPasswordRequestResponse(message=FORGOT_PASSWORD_GENERIC_MESSAGE)

    _, password_hash = hash_student_default_password(target_user.last_name)
    target_user.password_hash = password_hash
    target_user.using_default_import_password = True
    target_user.must_change_password = must_change_password_for_new_account()
    target_user.should_prompt_password_change = should_prompt_password_change_for_new_account()

    (
        db.query(PasswordResetRequest)
        .filter(
            PasswordResetRequest.user_id == target_user.id,
            PasswordResetRequest.status == "pending",
        )
        .update(
            {
                "status": "auto_reset",
                "resolved_at": utc_now(),
                "reviewed_by_user_id": None,
            },
            synchronize_session=False,
        )
    )
    db.commit()

    return ForgotPasswordRequestResponse(message=FORGOT_PASSWORD_GENERIC_MESSAGE)


@router.get("/auth/password-reset-requests", response_model=list[PasswordResetRequestItem])
def list_password_reset_requests(
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    is_platform_admin = _is_platform_admin_account(current_user)

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
    if not is_platform_admin:
        requests = [
            item
            for item in requests
            if item.user is not None
            and not _requires_platform_admin_password_reset_approval(item.user)
        ]

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
def approve_password_reset_request(
    request_id: int,
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
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

    is_platform_admin = _is_platform_admin_account(current_user)
    if not is_platform_admin:
        actor_school_id = getattr(current_user, "school_id", None)
        if actor_school_id is None or actor_school_id != request_item.school_id:
            raise HTTPException(status_code=404, detail="Password reset request not found")

    target_user = request_item.user
    if not getattr(target_user, "is_active", True):
        raise HTTPException(status_code=400, detail="Target user is inactive")

    if has_any_role(current_user, ["campus_admin"]) and not has_any_role(current_user, ["admin"]):
        if _requires_platform_admin_password_reset_approval(target_user):
            raise HTTPException(
                status_code=403,
                detail="Campus Admin cannot reset admin or Campus Admin accounts.",
            )
        if current_user.id == target_user.id:
            raise HTTPException(status_code=403, detail="Campus Admin cannot approve their own reset request.")

    temporary_password = generate_secure_password(min_length=10, max_length=14)
    target_user.set_password(temporary_password)
    target_user.must_change_password = must_change_password_for_temporary_reset()
    target_user.should_prompt_password_change = False

    request_item.status = "approved"
    request_item.resolved_at = utc_now()
    request_item.reviewed_by_user_id = current_user.id

    try:
        send_account_security_notification(
            db,
            user=target_user,
            subject="Password Reset Approved",
            message="Your password reset request was approved. Email delivery is disabled for now.",
            metadata_json={"event": "password_reset_approved", "request_id": request_item.id},
        )
    except Exception:
        pass

    db.commit()

    return PasswordResetApprovalResponse(
        id=request_item.id,
        user_id=target_user.id,
        status=request_item.status,
        resolved_at=request_item.resolved_at or utc_now(),
        message="Password reset approved. Email delivery is disabled for now.",
    )


from __future__ import annotations

import logging
from typing import Any

from fastapi import BackgroundTasks

from app.database import SessionLocal
from app.models.user import User as UserModel
from app.services.email_service import (
    EmailDeliveryError,
    send_mfa_code_email,
    validate_email_delivery_settings,
)
from app.services.notification_center_service import send_account_security_notification
from app.worker.tasks import (
    send_login_mfa_code_email,
    send_login_security_notification,
)

logger = logging.getLogger(__name__)


def _enqueue_celery_task(task: Any, *args: object, **kwargs: object) -> bool:
    try:
        task.apply_async(args=args, kwargs=kwargs, retry=False)
        return True
    except Exception:
        logger.warning(
            "Falling back to in-process background execution for task %s.",
            getattr(task, "name", repr(task)),
            exc_info=True,
        )
        return False


def _send_account_security_notification_in_process(
    *,
    user_id: int,
    subject: str,
    message: str,
    metadata_json: dict[str, object] | None = None,
) -> None:
    with SessionLocal() as db:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user is None:
            logger.warning(
                "Skipped account security notification because user %s was not found.",
                user_id,
            )
            return
        send_account_security_notification(
            db,
            user=user,
            subject=subject,
            message=message,
            metadata_json=metadata_json,
        )
        db.commit()


def dispatch_mfa_code_email(
    background_tasks: BackgroundTasks,
    *,
    recipient_email: str,
    code: str,
    first_name: str | None = None,
    system_name: str | None = None,
) -> str:
    validate_email_delivery_settings()
    if _enqueue_celery_task(
        send_login_mfa_code_email,
        recipient_email,
        code,
        first_name,
        system_name,
    ):
        return "celery"

    background_tasks.add_task(
        send_mfa_code_email,
        recipient_email=recipient_email,
        code=code,
        first_name=first_name,
        system_name=system_name,
    )
    return "background"


def dispatch_account_security_notification(
    background_tasks: BackgroundTasks,
    *,
    user_id: int,
    subject: str,
    message: str,
    metadata_json: dict[str, object] | None = None,
) -> str:
    if _enqueue_celery_task(
        send_login_security_notification,
        user_id,
        subject,
        message,
        metadata_json,
    ):
        return "celery"

    background_tasks.add_task(
        _send_account_security_notification_in_process,
        user_id=user_id,
        subject=subject,
        message=message,
        metadata_json=metadata_json,
    )
    return "background"


__all__ = [
    "dispatch_account_security_notification",
    "dispatch_mfa_code_email",
]

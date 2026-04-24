"""Use: Defines the main backend background tasks.
Where to use: Use this when work should run outside the request cycle, such as imports or scheduled jobs.
Role: Worker execution layer. It runs long or scheduled backend work.
"""

from __future__ import annotations

import logging

from app.core.database import SessionLocal
from app.models.user import User as UserModel
from app.repositories.import_repository import ImportRepository
from app.services.email_service import (
    EmailDeliveryError,
    send_import_onboarding_email,
    send_plain_email,
    send_welcome_email,
)
from app.services.event_workflow_status import (
    summarize_event_workflow_status_sync,
    sync_scope_event_workflow_statuses,
)
from app.services.notification_center_service import send_account_security_notification
from app.services.student_import_service import StudentImportService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _process_student_import_job(job_id: str) -> None:
    service = StudentImportService()
    service.process_job(job_id)


process_student_import_job = celery_app.task(
    name="app.workers.tasks.process_student_import_job",
)(_process_student_import_job)


def _sync_event_workflow_statuses() -> dict[str, int]:
    with SessionLocal() as db:
        results = sync_scope_event_workflow_statuses(db)
        summary = summarize_event_workflow_status_sync(results)
        if summary.changed_events > 0:
            db.commit()

        payload = {
            "scanned_events": summary.scanned_events,
            "changed_events": summary.changed_events,
            "moved_to_upcoming": summary.moved_to_upcoming,
            "moved_to_ongoing": summary.moved_to_ongoing,
            "moved_to_completed": summary.moved_to_completed,
            "attendance_finalized_events": summary.attendance_finalized_events,
            "absent_records_created": summary.absent_records_created,
            "absent_no_timeout_marked": summary.absent_no_timeout_marked,
            "sanction_records_created": summary.sanction_records_created,
            "sanction_notification_emails_queued": summary.sanction_notification_emails_queued,
        }
        logger.info("Automatic event workflow sync completed: %s", payload)
        return payload


sync_event_workflow_statuses = celery_app.task(
    name="app.workers.tasks.sync_event_workflow_statuses",
)(_sync_event_workflow_statuses)


def _send_student_welcome_email(
    self,
    job_id: str,
    user_id: int,
    email: str,
    temporary_password: str,
    first_name: str | None = None,
) -> None:
    try:
        send_welcome_email(
            recipient_email=email,
            temporary_password=temporary_password,
            first_name=first_name,
        )
        with SessionLocal() as db:
            repo = ImportRepository(db)
            repo.log_email_delivery(
                job_id=job_id,
                user_id=user_id,
                email=email,
                status="sent",
                retry_count=self.request.retries,
            )
            db.commit()
    except Exception as exc:
        with SessionLocal() as db:
            repo = ImportRepository(db)
            repo.log_email_delivery(
                job_id=job_id,
                user_id=user_id,
                email=email,
                status="failed",
                error_message=str(exc),
                retry_count=self.request.retries,
            )
            db.commit()
        raise


def _send_student_import_onboarding_email(
    self,
    job_id: str,
    user_id: int,
    email: str,
    first_name: str | None = None,
    temporary_password: str | None = None,
) -> None:
    try:
        send_import_onboarding_email(
            recipient_email=email,
            first_name=first_name,
            temporary_password=temporary_password or "",
        )
        with SessionLocal() as db:
            repo = ImportRepository(db)
            repo.log_email_delivery(
                job_id=job_id,
                user_id=user_id,
                email=email,
                status="sent",
                retry_count=self.request.retries,
            )
            db.commit()
    except Exception as exc:
        with SessionLocal() as db:
            repo = ImportRepository(db)
            repo.log_email_delivery(
                job_id=job_id,
                user_id=user_id,
                email=email,
                status="failed",
                error_message=str(exc),
                retry_count=self.request.retries,
            )
            db.commit()
        raise


send_student_welcome_email = celery_app.task(
    bind=True,
    name="app.workers.tasks.send_student_welcome_email",
    autoretry_for=(EmailDeliveryError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)(_send_student_welcome_email)

send_student_import_onboarding_email = celery_app.task(
    bind=True,
    name="app.workers.tasks.send_student_import_onboarding_email",
    autoretry_for=(EmailDeliveryError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)(_send_student_import_onboarding_email)


def _send_sanction_notification_email(
    self,
    recipient_email: str,
    first_name: str | None,
    event_name: str,
    sanction_item_names: list[str] | None = None,
) -> None:
    resolved_first_name = (first_name or "").strip() or "Student"
    normalized_item_names = [name.strip() for name in (sanction_item_names or []) if name and name.strip()]
    items_block = "\n".join(f"- {item_name}" for item_name in normalized_item_names)
    body_lines = [
        f"Hello {resolved_first_name},",
        "",
        f"You were marked absent for the event: {event_name}.",
        "A sanctions record has been generated for your account.",
    ]
    if items_block:
        body_lines.extend(
            [
                "",
                "Sanction items:",
                items_block,
            ]
        )
    body_lines.extend(
        [
            "",
            "Please coordinate with your governance office for compliance instructions.",
            "",
            "Aura",
        ]
    )
    send_plain_email(
        recipient_email=recipient_email,
        subject=f"Sanction Notice - {event_name}",
        body="\n".join(body_lines),
    )


send_sanction_notification_email = celery_app.task(
    bind=True,
    name="app.workers.tasks.send_sanction_notification_email",
    autoretry_for=(EmailDeliveryError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)(_send_sanction_notification_email)


def _send_clearance_deadline_warning_email(
    self,
    recipient_email: str,
    first_name: str | None,
    event_name: str,
    deadline_at_iso: str,
    message: str | None = None,
) -> None:
    resolved_first_name = (first_name or "").strip() or "Student"
    body_lines = [
        f"Hello {resolved_first_name},",
        "",
        f"An SSG clearance deadline was posted for event sanctions: {event_name}.",
        f"Deadline: {deadline_at_iso}",
    ]
    if message:
        body_lines.extend(
            [
                "",
                "Message:",
                message.strip(),
            ]
        )
    body_lines.extend(
        [
            "",
            "Please complete pending sanctions before the deadline.",
            "",
            "Aura",
        ]
    )
    send_plain_email(
        recipient_email=recipient_email,
        subject=f"Sanctions Clearance Deadline - {event_name}",
        body="\n".join(body_lines),
    )


send_clearance_deadline_warning_email = celery_app.task(
    bind=True,
    name="app.workers.tasks.send_clearance_deadline_warning_email",
    autoretry_for=(EmailDeliveryError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)(_send_clearance_deadline_warning_email)


def _send_sanction_compliance_confirmation_email(
    self,
    recipient_email: str,
    first_name: str | None,
    event_name: str,
) -> None:
    resolved_first_name = (first_name or "").strip() or "Student"
    body_lines = [
        f"Hello {resolved_first_name},",
        "",
        f"Your sanctions for event {event_name} were marked as complied.",
        "",
        "If this is incorrect, contact your governance office immediately.",
        "",
        "Aura",
    ]
    send_plain_email(
        recipient_email=recipient_email,
        subject=f"Sanction Compliance Confirmed - {event_name}",
        body="\n".join(body_lines),
    )


send_sanction_compliance_confirmation_email = celery_app.task(
    bind=True,
    name="app.workers.tasks.send_sanction_compliance_confirmation_email",
    autoretry_for=(EmailDeliveryError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)(_send_sanction_compliance_confirmation_email)


def _send_login_security_notification(
    user_id: int,
    subject: str,
    message: str,
    metadata_json: dict[str, object] | None = None,
) -> None:
    with SessionLocal() as db:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user is None:
            logger.warning(
                "Skipped login security notification because user %s was not found.",
                user_id,
            )
            return
        try:
            send_account_security_notification(
                db,
                user=user,
                subject=subject,
                message=message,
                metadata_json=metadata_json,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise


send_login_security_notification = celery_app.task(
    name="app.workers.tasks.send_login_security_notification",
)(_send_login_security_notification)


__all__ = [
    "process_student_import_job",
    "send_clearance_deadline_warning_email",
    "send_login_security_notification",
    "send_sanction_compliance_confirmation_email",
    "send_sanction_notification_email",
    "send_student_import_onboarding_email",
    "send_student_welcome_email",
    "sync_event_workflow_statuses",
]

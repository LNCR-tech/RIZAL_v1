from __future__ import annotations

import logging

from app.database import SessionLocal
from app.models.user import User as UserModel
from app.repositories.import_repository import ImportRepository
from app.services.email_service import (
    EmailDeliveryError,
    send_mfa_code_email,
    send_welcome_email,
)
from app.services.event_workflow_status import (
    summarize_event_workflow_status_sync,
    sync_scope_event_workflow_statuses,
)
from app.services.notification_center_service import send_account_security_notification
from app.services.student_import_service import StudentImportService
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.worker.tasks.process_student_import_job")
def process_student_import_job(job_id: str) -> None:
    service = StudentImportService()
    service.process_job(job_id)


@celery_app.task(name="app.worker.tasks.sync_event_workflow_statuses")
def sync_event_workflow_statuses() -> dict[str, int]:
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
        }
        logger.info("Automatic event workflow sync completed: %s", payload)
        return payload


@celery_app.task(
    bind=True,
    name="app.worker.tasks.send_student_welcome_email",
    autoretry_for=(EmailDeliveryError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_student_welcome_email(
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


@celery_app.task(
    bind=True,
    name="app.worker.tasks.send_login_mfa_code_email",
    autoretry_for=(EmailDeliveryError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_login_mfa_code_email(
    self,
    recipient_email: str,
    code: str,
    first_name: str | None = None,
    system_name: str | None = None,
) -> None:
    send_mfa_code_email(
        recipient_email=recipient_email,
        code=code,
        first_name=first_name,
        system_name=system_name,
    )


@celery_app.task(name="app.worker.tasks.send_login_security_notification")
def send_login_security_notification(
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

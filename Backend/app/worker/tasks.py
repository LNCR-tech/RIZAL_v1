from __future__ import annotations

from app.database import SessionLocal
from app.repositories.import_repository import ImportRepository
from app.services.email_service import EmailDeliveryError, send_welcome_email
from app.services.student_import_service import StudentImportService
from app.worker.celery_app import celery_app


@celery_app.task(name="app.worker.tasks.process_student_import_job")
def process_student_import_job(job_id: str) -> None:
    service = StudentImportService()
    service.process_job(job_id)


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

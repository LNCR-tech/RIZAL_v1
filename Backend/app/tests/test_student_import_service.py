"""Use: Tests fallback onboarding email behavior in student bulk import processing.
Where to use: Run this with pytest to verify that import onboarding emails are still attempted when Celery is unavailable.
Role: Test layer. It protects bulk import onboarding delivery behavior from regressions.
"""

from __future__ import annotations

from sqlalchemy.orm import sessionmaker

from app.models import EmailDeliveryLog, School, User
from app.services.student_import_service import StudentImportService


def _create_school(test_db, *, code: str) -> School:
    school = School(
        name=f"Import Service School {code}",
        school_name=f"Import Service School {code}",
        school_code=code,
        address="Import Service Test Address",
    )
    test_db.add(school)
    test_db.commit()
    return school


def _create_user(
    test_db,
    *,
    school_id: int,
    email: str,
    first_name: str = "Import",
    last_name: str = "Student",
) -> User:
    user = User(
        email=email,
        school_id=school_id,
        first_name=first_name,
        last_name=last_name,
        must_change_password=True,
        should_prompt_password_change=True,
    )
    user.set_password("ImportPass123!")
    test_db.add(user)
    test_db.commit()
    return user


def test_queue_account_ready_email_falls_back_to_inline_delivery_when_publish_fails(
    test_db,
    monkeypatch,
):
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_db.get_bind())
    monkeypatch.setattr("app.services.student_import_service.SessionLocal", session_local)

    school = _create_school(test_db, code="SERVICE-EMAIL-FALLBACK")
    user = _create_user(
        test_db,
        school_id=school.id,
        email="inline.fallback@example.edu",
        first_name="Inline",
    )

    sent_calls: list[tuple[str, str | None]] = []

    def _raise_send_task(*_args, **_kwargs):
        raise RuntimeError("celery broker unavailable")

    def _fake_send_import_onboarding_email(*, recipient_email: str, first_name: str | None = None, **_kwargs):
        sent_calls.append((recipient_email, first_name))

    monkeypatch.setattr("app.services.student_import_service.celery_app.send_task", _raise_send_task)
    monkeypatch.setattr(
        "app.services.student_import_service.send_import_onboarding_email",
        _fake_send_import_onboarding_email,
    )

    service = StudentImportService()
    service._queue_account_ready_email(
        job_id="job-inline-fallback",
        user_id=user.id,
        email=user.email,
        first_name=user.first_name,
        temporary_password="TempPass123!",
    )

    assert sent_calls == [(user.email, user.first_name)]

    test_db.expire_all()
    log_entry = (
        test_db.query(EmailDeliveryLog)
        .filter(EmailDeliveryLog.job_id == "job-inline-fallback")
        .one()
    )
    assert log_entry.status == "sent"
    assert log_entry.error_message is None


def test_queue_account_ready_email_logs_failed_when_publish_and_inline_delivery_fail(
    test_db,
    monkeypatch,
):
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_db.get_bind())
    monkeypatch.setattr("app.services.student_import_service.SessionLocal", session_local)

    school = _create_school(test_db, code="SERVICE-EMAIL-FAILURE")
    user = _create_user(
        test_db,
        school_id=school.id,
        email="inline.failure@example.edu",
        first_name="Failure",
    )

    def _raise_send_task(*_args, **_kwargs):
        raise RuntimeError("celery broker unavailable")

    def _raise_inline_send(*, recipient_email: str, first_name: str | None = None, **_kwargs):
        raise RuntimeError("smtp provider unavailable")

    monkeypatch.setattr("app.services.student_import_service.celery_app.send_task", _raise_send_task)
    monkeypatch.setattr(
        "app.services.student_import_service.send_import_onboarding_email",
        _raise_inline_send,
    )

    service = StudentImportService()
    service._queue_account_ready_email(
        job_id="job-inline-failed",
        user_id=user.id,
        email=user.email,
        first_name=user.first_name,
        temporary_password="TempPass123!",
    )

    test_db.expire_all()
    log_entry = (
        test_db.query(EmailDeliveryLog)
        .filter(EmailDeliveryLog.job_id == "job-inline-failed")
        .one()
    )
    assert log_entry.status == "failed"
    assert log_entry.error_message is not None
    assert "Celery publish failed: celery broker unavailable." in log_entry.error_message
    assert "Inline delivery failed: smtp provider unavailable" in log_entry.error_message

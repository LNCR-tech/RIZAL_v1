"""Use: Tests bulk-import onboarding email dispatch behavior.
Where to use: Use this when running `pytest` to verify imported accounts still trigger email delivery work.
Role: Test layer. It protects the import-to-email handoff from regressions.
"""

from types import SimpleNamespace

from app.services.student_import_service import StudentImportService
from app.workers import tasks as worker_tasks


class _DummySession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self) -> None:
        return None


def test_queue_account_ready_email_publishes_import_onboarding_task(monkeypatch) -> None:
    queued: list[tuple[str, list[object]]] = []

    def fake_send_task(name: str, args: list[object]):
        queued.append((name, list(args)))
        return None

    monkeypatch.setattr("app.services.student_import_service.celery_app.send_task", fake_send_task)

    StudentImportService()._queue_account_ready_email(
        job_id="job-1",
        user_id=7,
        email="student@example.com",
        first_name="Student",
        temporary_password="ImportPass123!",
    )

    assert queued == [
        (
            "app.workers.tasks.send_student_import_onboarding_email",
            ["job-1", 7, "student@example.com", "Student", "ImportPass123!"],
        )
    ]


def test_queue_account_ready_email_falls_back_to_inline_send_when_publish_fails(monkeypatch) -> None:
    sent: list[dict[str, object]] = []
    logged: list[dict[str, object]] = []

    class FakeImportRepository:
        def __init__(self, db):
            self.db = db

        def log_email_delivery(self, **kwargs) -> None:
            logged.append(dict(kwargs))

    def failing_send_task(name: str, args: list[object]):
        raise RuntimeError("broker unavailable")

    def fake_send_import_onboarding_email(
        *,
        recipient_email: str,
        first_name: str | None = None,
        temporary_password: str,
    ) -> None:
        sent.append(
            {
                "recipient_email": recipient_email,
                "first_name": first_name,
                "temporary_password": temporary_password,
            }
        )

    monkeypatch.setattr("app.services.student_import_service.celery_app.send_task", failing_send_task)
    monkeypatch.setattr(
        "app.services.student_import_service.send_import_onboarding_email",
        fake_send_import_onboarding_email,
    )
    monkeypatch.setattr("app.services.student_import_service.SessionLocal", lambda: _DummySession())
    monkeypatch.setattr("app.services.student_import_service.ImportRepository", FakeImportRepository)

    StudentImportService()._queue_account_ready_email(
        job_id="job-2",
        user_id=9,
        email="deferred@example.com",
        first_name="Deferred",
        temporary_password="ImportPass123!",
    )

    assert sent == [
        {
            "recipient_email": "deferred@example.com",
            "first_name": "Deferred",
            "temporary_password": "ImportPass123!",
        }
    ]
    assert logged == [
        {
            "job_id": "job-2",
            "user_id": 9,
            "email": "deferred@example.com",
            "status": "sent",
            "error_message": None,
            "retry_count": 0,
        }
    ]


def test_queue_account_ready_email_logs_failed_when_publish_and_inline_send_fail(monkeypatch) -> None:
    logged: list[dict[str, object]] = []

    class FakeImportRepository:
        def __init__(self, db):
            self.db = db

        def log_email_delivery(self, **kwargs) -> None:
            logged.append(dict(kwargs))

    def failing_send_task(name: str, args: list[object]):
        raise RuntimeError("broker unavailable")

    def failing_send_import_onboarding_email(
        *,
        recipient_email: str,
        first_name: str | None = None,
        temporary_password: str,
    ) -> None:
        raise RuntimeError("gmail api down")

    monkeypatch.setattr("app.services.student_import_service.celery_app.send_task", failing_send_task)
    monkeypatch.setattr(
        "app.services.student_import_service.send_import_onboarding_email",
        failing_send_import_onboarding_email,
    )
    monkeypatch.setattr("app.services.student_import_service.SessionLocal", lambda: _DummySession())
    monkeypatch.setattr("app.services.student_import_service.ImportRepository", FakeImportRepository)

    StudentImportService()._queue_account_ready_email(
        job_id="job-2b",
        user_id=10,
        email="failed@example.com",
        first_name="Failed",
        temporary_password="ImportPass123!",
    )

    assert logged == [
        {
            "job_id": "job-2b",
            "user_id": 10,
            "email": "failed@example.com",
            "status": "failed",
            "error_message": "Task publish failed: broker unavailable; inline send failed: gmail api down",
            "retry_count": 0,
        }
    ]


def test_send_student_import_onboarding_email_logs_sent_delivery(monkeypatch) -> None:
    sent: list[dict[str, object]] = []
    logged: list[dict[str, object]] = []

    class FakeImportRepository:
        def __init__(self, db):
            self.db = db

        def log_email_delivery(self, **kwargs) -> None:
            logged.append(dict(kwargs))

    def fake_send_import_onboarding_email(
        *,
        recipient_email: str,
        first_name: str | None = None,
        temporary_password: str,
    ) -> None:
        sent.append(
            {
                "recipient_email": recipient_email,
                "first_name": first_name,
                "temporary_password": temporary_password,
            }
        )

    monkeypatch.setattr(worker_tasks, "send_import_onboarding_email", fake_send_import_onboarding_email)
    monkeypatch.setattr(worker_tasks, "SessionLocal", lambda: _DummySession())
    monkeypatch.setattr(worker_tasks, "ImportRepository", FakeImportRepository)

    task_self = SimpleNamespace(request=SimpleNamespace(retries=0))
    worker_tasks._send_student_import_onboarding_email(
        task_self,
        "job-3",
        11,
        "imported@example.com",
        "Imported",
        "ImportPass123!",
    )

    assert sent == [
        {
            "recipient_email": "imported@example.com",
            "first_name": "Imported",
            "temporary_password": "ImportPass123!",
        }
    ]
    assert logged == [
        {
            "job_id": "job-3",
            "user_id": 11,
            "email": "imported@example.com",
            "status": "sent",
            "retry_count": 0,
        }
    ]

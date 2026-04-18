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


def test_attach_import_password_credentials_generates_unique_values_per_row(monkeypatch) -> None:
    generated_passwords = iter(["ImportPass111A", "ImportPass222B"])

    monkeypatch.setattr(
        "app.services.student_import_service.generate_secure_password",
        lambda min_length=10, max_length=14: next(generated_passwords),
    )
    monkeypatch.setattr(
        "app.services.student_import_service.hash_password_bcrypt",
        lambda password: f"hash::{password}",
    )

    service = StudentImportService()
    rows = [{}, {}]

    service._attach_import_password_credentials_batch(rows)

    assert rows[0]["temporary_password"] == "ImportPass111A"
    assert rows[0]["password_hash"] == "hash::ImportPass111A"
    assert rows[1]["temporary_password"] == "ImportPass222B"
    assert rows[1]["password_hash"] == "hash::ImportPass222B"


def test_attach_import_password_credentials_batch_retries_duplicate_passwords(monkeypatch) -> None:
    generated_passwords = iter(["ImportPass111A", "ImportPass111A", "ImportPass222B"])

    monkeypatch.setattr(
        "app.services.student_import_service.generate_secure_password",
        lambda min_length=10, max_length=14: next(generated_passwords),
    )
    monkeypatch.setattr(
        "app.services.student_import_service.hash_password_bcrypt",
        lambda password: f"hash::{password}",
    )

    service = StudentImportService()
    rows = [{}, {}]

    service._attach_import_password_credentials_batch(rows, used_temporary_passwords=set())

    assert rows[0]["temporary_password"] == "ImportPass111A"
    assert rows[1]["temporary_password"] == "ImportPass222B"
    assert rows[0]["temporary_password"] != rows[1]["temporary_password"]
    assert rows[0]["password_hash"] == "hash::ImportPass111A"
    assert rows[1]["password_hash"] == "hash::ImportPass222B"


def test_flush_batch_queues_email_with_each_row_temporary_password(monkeypatch) -> None:
    queued: list[dict[str, object]] = []

    class FakeImportRepository:
        def __init__(self, db):
            self.db = db

        def bulk_insert_students(self, rows, student_role_id, trust_preview=False):
            return [
                {**rows[0], "user_id": 101},
                {**rows[1], "user_id": 102},
            ], []

    def fake_queue(
        self,
        *,
        job_id: str,
        user_id: int,
        email: str,
        first_name: str | None = None,
        temporary_password: str,
    ) -> None:
        queued.append(
            {
                "job_id": job_id,
                "user_id": user_id,
                "email": email,
                "first_name": first_name,
                "temporary_password": temporary_password,
            }
        )

    monkeypatch.setattr("app.services.student_import_service.SessionLocal", lambda: _DummySession())
    monkeypatch.setattr("app.services.student_import_service.ImportRepository", FakeImportRepository)
    monkeypatch.setattr(StudentImportService, "_queue_account_ready_email", fake_queue)

    service = StudentImportService()
    success_count, failed_count, errors = service._flush_batch(
        job_id="job-credentials",
        row_buffer=[
            {
                "email": "row.one@example.com",
                "first_name": "RowOne",
                "temporary_password": "ImportPass111A",
                "password_hash": "hash::ImportPass111A",
            },
            {
                "email": "row.two@example.com",
                "first_name": "RowTwo",
                "temporary_password": "ImportPass222B",
                "password_hash": "hash::ImportPass222B",
            },
        ],
        student_role_id=7,
    )

    assert success_count == 2
    assert failed_count == 0
    assert errors == []
    assert queued == [
        {
            "job_id": "job-credentials",
            "user_id": 101,
            "email": "row.one@example.com",
            "first_name": "RowOne",
            "temporary_password": "ImportPass111A",
        },
        {
            "job_id": "job-credentials",
            "user_id": 102,
            "email": "row.two@example.com",
            "first_name": "RowTwo",
            "temporary_password": "ImportPass222B",
        },
    ]

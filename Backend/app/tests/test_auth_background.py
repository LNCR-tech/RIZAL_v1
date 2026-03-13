from fastapi import BackgroundTasks

from app.services import auth_background


def test_dispatch_mfa_code_email_uses_celery_when_available(monkeypatch) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_validate() -> None:
        return None

    def fake_apply_async(*, args, kwargs, retry) -> None:
        calls.append((tuple(args), dict(kwargs)))
        assert retry is False

    monkeypatch.setattr(auth_background, "validate_email_delivery_settings", fake_validate)
    monkeypatch.setattr(
        auth_background.send_login_mfa_code_email,
        "apply_async",
        fake_apply_async,
    )

    background_tasks = BackgroundTasks()
    mode = auth_background.dispatch_mfa_code_email(
        background_tasks,
        recipient_email="user@example.com",
        code="123456",
        first_name="Test",
        system_name="VALID8",
    )

    assert mode == "celery"
    assert len(background_tasks.tasks) == 0
    assert calls == [
        (
            ("user@example.com", "123456", "Test", "VALID8"),
            {},
        )
    ]


def test_dispatch_mfa_code_email_falls_back_to_background_task(monkeypatch) -> None:
    def fake_validate() -> None:
        return None

    def fake_apply_async(*, args, kwargs, retry) -> None:
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(auth_background, "validate_email_delivery_settings", fake_validate)
    monkeypatch.setattr(
        auth_background.send_login_mfa_code_email,
        "apply_async",
        fake_apply_async,
    )

    background_tasks = BackgroundTasks()
    mode = auth_background.dispatch_mfa_code_email(
        background_tasks,
        recipient_email="user@example.com",
        code="123456",
    )

    assert mode == "background"
    assert len(background_tasks.tasks) == 1
    assert background_tasks.tasks[0].func is auth_background.send_mfa_code_email


def test_dispatch_account_security_notification_falls_back_to_background_task(monkeypatch) -> None:
    def fake_apply_async(*, args, kwargs, retry) -> None:
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(
        auth_background.send_login_security_notification,
        "apply_async",
        fake_apply_async,
    )

    background_tasks = BackgroundTasks()
    mode = auth_background.dispatch_account_security_notification(
        background_tasks,
        user_id=7,
        subject="New Login Detected",
        message="Security event.",
        metadata_json={"event": "login"},
    )

    assert mode == "background"
    assert len(background_tasks.tasks) == 1

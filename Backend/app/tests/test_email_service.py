from types import SimpleNamespace

from app.services import email_service


def test_send_welcome_email_allows_temporary_password_after_login(monkeypatch) -> None:
    sent: dict[str, str] = {}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: SimpleNamespace(login_url="https://valid8.example/login"),
    )

    def fake_send_email(subject: str, recipient_email: str, body: str) -> None:
        sent["subject"] = subject
        sent["recipient_email"] = recipient_email
        sent["body"] = body

    monkeypatch.setattr(email_service, "_send_email", fake_send_email)

    email_service.send_welcome_email(
        recipient_email="new.user@example.com",
        temporary_password="TempPass123!",
        first_name="New",
        system_name="VALID8",
    )

    assert sent["recipient_email"] == "new.user@example.com"
    assert "You can keep using it after login" in sent["body"]
    assert (
        "You are required to change your password immediately after your first login."
        not in sent["body"]
    )


def test_send_password_reset_email_still_requires_password_change(monkeypatch) -> None:
    sent: dict[str, str] = {}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: SimpleNamespace(login_url="https://valid8.example/login"),
    )

    def fake_send_email(subject: str, recipient_email: str, body: str) -> None:
        sent["subject"] = subject
        sent["recipient_email"] = recipient_email
        sent["body"] = body

    monkeypatch.setattr(email_service, "_send_email", fake_send_email)

    email_service.send_password_reset_email(
        recipient_email="existing.user@example.com",
        temporary_password="TempPass123!",
        first_name="Existing",
        system_name="VALID8",
    )

    assert sent["recipient_email"] == "existing.user@example.com"
    assert "You are required to change this temporary password immediately after login." in sent["body"]


def test_send_welcome_email_with_user_supplied_password_uses_generic_password_copy(monkeypatch) -> None:
    sent: dict[str, str] = {}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: SimpleNamespace(login_url="https://valid8.example/login"),
    )

    def fake_send_email(subject: str, recipient_email: str, body: str) -> None:
        sent["subject"] = subject
        sent["recipient_email"] = recipient_email
        sent["body"] = body

    monkeypatch.setattr(email_service, "_send_email", fake_send_email)

    email_service.send_welcome_email(
        recipient_email="provided.password@example.com",
        temporary_password="ChosenPass123!",
        first_name="Chosen",
        system_name="VALID8",
        password_is_temporary=False,
    )

    assert sent["recipient_email"] == "provided.password@example.com"
    assert "Password: ChosenPass123!" in sent["body"]
    assert "Temporary Password:" not in sent["body"]
    assert "You can change it anytime from your account settings" in sent["body"]

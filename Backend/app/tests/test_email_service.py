"""Use: Tests Mailjet-backed email service behavior.
Where to use: Use this when running `pytest` to check that this backend behavior still works.
Role: Test layer. It protects the app from regressions.
"""

import json
from types import SimpleNamespace

from app.services import email_service


def _mailjet_settings(**overrides):
    defaults = {
        "email_transport": "mailjet_api",
        "email_verify_connection_on_startup": False,
        "email_timeout_seconds": 20,
        "email_sender_email": "mailer@example.com",
        "email_sender_name": "Aura Notifications",
        "email_reply_to": "",
        "mailjet_api_key": "mailjet-key",
        "mailjet_api_secret": "mailjet-secret",
        "mailjet_api_base_url": "https://api.mailjet.com/v3.1/send",
        "login_url": "https://aura.example/login",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_send_welcome_email_allows_temporary_password_after_login(monkeypatch) -> None:
    sent: dict[str, str] = {}

    def fake_send_email(*, subject: str, recipient_email: str, body: str, **kwargs) -> None:
        sent["subject"] = subject
        sent["recipient_email"] = recipient_email
        sent["body"] = body
        sent["html_body"] = kwargs.get("html_body") or ""

    monkeypatch.setattr(email_service, "_send_email", fake_send_email)

    email_service.send_welcome_email(
        recipient_email="new.user@example.com",
        temporary_password="TempPass123!",
        first_name="New",
        system_name="Aura",
    )

    assert sent["recipient_email"] == "new.user@example.com"
    assert "You can keep using it after login" in sent["body"]
    assert "https://supervirulently-downless-keven.ngrok-free.dev" in sent["body"]
    assert (
        "You are required to change your password immediately after your first login."
        not in sent["body"]
    )
    assert "Login Credentials" in sent["html_body"]


def test_send_password_reset_email_still_requires_password_change(monkeypatch) -> None:
    sent: dict[str, str] = {}

    def fake_send_email(*, subject: str, recipient_email: str, body: str, **kwargs) -> None:
        sent["subject"] = subject
        sent["recipient_email"] = recipient_email
        sent["body"] = body
        sent["html_body"] = kwargs.get("html_body") or ""

    monkeypatch.setattr(email_service, "_send_email", fake_send_email)

    email_service.send_password_reset_email(
        recipient_email="existing.user@example.com",
        temporary_password="TempPass123!",
        first_name="Existing",
        system_name="Aura",
    )

    assert sent["recipient_email"] == "existing.user@example.com"
    assert "You are required to change this temporary password immediately after login." in sent["body"]
    assert "https://supervirulently-downless-keven.ngrok-free.dev" in sent["body"]
    assert "Temporary Login Credentials" in sent["html_body"]


def test_send_welcome_email_with_user_supplied_password_uses_generic_password_copy(monkeypatch) -> None:
    sent: dict[str, str] = {}

    def fake_send_email(*, subject: str, recipient_email: str, body: str, **kwargs) -> None:
        sent["subject"] = subject
        sent["recipient_email"] = recipient_email
        sent["body"] = body

    monkeypatch.setattr(email_service, "_send_email", fake_send_email)

    email_service.send_welcome_email(
        recipient_email="provided.password@example.com",
        temporary_password="ChosenPass123!",
        first_name="Chosen",
        system_name="Aura",
        password_is_temporary=False,
    )

    assert sent["recipient_email"] == "provided.password@example.com"
    assert "Password: ChosenPass123!" in sent["body"]
    assert "Temporary Password:" not in sent["body"]
    assert "You can change it anytime from your account settings" in sent["body"]


def test_send_import_onboarding_email_matches_welcome_credentials_copy(monkeypatch) -> None:
    sent: dict[str, str] = {}

    def fake_send_email(*, subject: str, recipient_email: str, body: str, **kwargs) -> None:
        sent["subject"] = subject
        sent["recipient_email"] = recipient_email
        sent["body"] = body
        sent["html_body"] = kwargs.get("html_body") or ""

    monkeypatch.setattr(email_service, "_send_email", fake_send_email)

    email_service.send_import_onboarding_email(
        recipient_email="imported.user@example.com",
        temporary_password="ImportPass123!",
        first_name="Imported",
        system_name="Aura",
    )

    assert sent["recipient_email"] == "imported.user@example.com"
    assert "Email: imported.user@example.com" in sent["body"]
    assert "Temporary Password: ImportPass123!" in sent["body"]
    assert "Login URL: https://supervirulently-downless-keven.ngrok-free.dev" in sent["body"]
    assert "Forgot Password option" not in sent["body"]
    assert "Login Credentials" in sent["html_body"]


def test_validate_email_delivery_settings_accepts_mailjet_transport() -> None:
    resolved = email_service.validate_email_delivery_settings(_mailjet_settings())

    assert resolved.transport == "mailjet_api"
    assert resolved.auth_mode == "basic"
    assert resolved.sender_email == "mailer@example.com"
    assert resolved.sender_name == "Aura Notifications"


def test_validate_email_delivery_settings_rejects_disabled_transport() -> None:
    try:
        email_service.validate_email_delivery_settings(
            _mailjet_settings(email_transport="disabled"),
        )
    except email_service.EmailConfigurationError as exc:
        assert "EMAIL_TRANSPORT is disabled" in str(exc)
    else:
        raise AssertionError("Expected EmailConfigurationError for disabled email transport")


def test_validate_email_delivery_settings_rejects_missing_mailjet_credentials() -> None:
    try:
        email_service.validate_email_delivery_settings(
            _mailjet_settings(mailjet_api_secret=""),
        )
    except email_service.EmailConfigurationError as exc:
        assert "MAILJET_API_SECRET" in str(exc)
    else:
        raise AssertionError("Expected EmailConfigurationError for missing Mailjet settings")


def test_check_email_delivery_connection_verifies_mailjet_transport(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeResponse:
        status_code = 200
        reason_phrase = "OK"
        text = json.dumps({"Count": 1, "Data": [{"Email": "mailer@example.com"}]})

        def json(self):
            return {"Count": 1, "Data": [{"Email": "mailer@example.com"}]}

    def fake_get(url: str, auth=None, headers=None, timeout=None):
        calls.append(
            {
                "url": url,
                "auth": auth,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return FakeResponse()

    monkeypatch.setattr(email_service.httpx, "get", fake_get)

    status = email_service.check_email_delivery_connection(settings=_mailjet_settings())

    assert status.transport == "mailjet_api"
    assert status.host == "api.mailjet.com"
    assert status.port == 443
    assert calls[0]["url"] == "https://api.mailjet.com/v3/REST/sender"
    assert calls[0]["auth"] == ("mailjet-key", "mailjet-secret")


def test_send_plain_email_uses_mailjet_transport(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        status_code = 200
        reason_phrase = "OK"
        text = json.dumps({"Messages": [{"Status": "success"}]})

        def json(self):
            return {"Messages": [{"Status": "success"}]}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: _mailjet_settings(),
    )

    def fake_post(url: str, auth=None, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["auth"] = auth
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(email_service.httpx, "post", fake_post)

    email_service.send_plain_email(
        recipient_email="recipient@example.com",
        subject="Subject",
        body="Body",
    )

    assert captured["url"] == "https://api.mailjet.com/v3.1/send"
    assert captured["auth"] == ("mailjet-key", "mailjet-secret")
    assert captured["json"]["Messages"][0]["From"] == {
        "Email": "mailer@example.com",
        "Name": "Aura Notifications",
    }
    assert captured["json"]["Messages"][0]["To"] == [{"Email": "recipient@example.com"}]
    assert captured["json"]["Messages"][0]["Subject"] == "Subject"
    assert captured["json"]["Messages"][0]["TextPart"] == "Body"


def test_send_plain_email_surfaces_mailjet_credential_errors(monkeypatch) -> None:
    class FakeResponse:
        status_code = 401
        reason_phrase = "Unauthorized"
        text = json.dumps({"ErrorMessage": "Unauthorized"})

        def json(self):
            return {"ErrorMessage": "Unauthorized"}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: _mailjet_settings(),
    )
    monkeypatch.setattr(email_service.httpx, "post", lambda *args, **kwargs: FakeResponse())

    try:
        email_service.send_plain_email(
            recipient_email="recipient@example.com",
            subject="Subject",
            body="Body",
        )
    except email_service.EmailDeliveryError as exc:
        assert "MAILJET_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected EmailDeliveryError for Mailjet credential failure")

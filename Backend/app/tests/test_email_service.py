"""Use: Tests Gmail API email service behavior.
Where to use: Use this when running `pytest` to check that this backend behavior still works.
Role: Test layer. It protects the app from regressions.
"""

import json
from types import SimpleNamespace

from app.services import email_service


def _gmail_api_settings(**overrides):
    defaults = {
        "email_transport": "gmail_api",
        "email_required_on_startup": True,
        "email_verify_connection_on_startup": False,
        "email_timeout_seconds": 20,
        "email_sender_email": "mailer@example.com",
        "email_from_email": "mailer@example.com",
        "email_from_name": "VALID8 Notifications",
        "email_reply_to": "",
        "email_google_account_type": "auto",
        "email_google_allow_custom_from": False,
        "google_oauth_client_id": "client-id",
        "google_oauth_client_secret": "client-secret",
        "google_oauth_refresh_token": "refresh-token",
        "google_oauth_auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "google_oauth_token_url": "https://oauth2.googleapis.com/token",
        "google_oauth_scopes": [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.settings.basic",
        ],
        "google_gmail_api_base_url": "https://gmail.googleapis.com/gmail/v1",
        "login_url": "https://valid8.example/login",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_send_welcome_email_allows_temporary_password_after_login(monkeypatch) -> None:
    sent: dict[str, str] = {}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: SimpleNamespace(login_url="https://valid8.example/login"),
    )

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
        system_name="VALID8",
    )

    assert sent["recipient_email"] == "new.user@example.com"
    assert "You can keep using it after login" in sent["body"]
    assert (
        "You are required to change your password immediately after your first login."
        not in sent["body"]
    )
    assert "Login Credentials" in sent["html_body"]


def test_send_password_reset_email_still_requires_password_change(monkeypatch) -> None:
    sent: dict[str, str] = {}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: SimpleNamespace(login_url="https://valid8.example/login"),
    )

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
        system_name="VALID8",
    )

    assert sent["recipient_email"] == "existing.user@example.com"
    assert "You are required to change this temporary password immediately after login." in sent["body"]
    assert "Temporary Login Credentials" in sent["html_body"]


def test_send_welcome_email_with_user_supplied_password_uses_generic_password_copy(monkeypatch) -> None:
    sent: dict[str, str] = {}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: SimpleNamespace(login_url="https://valid8.example/login"),
    )

    def fake_send_email(*, subject: str, recipient_email: str, body: str, **kwargs) -> None:
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


def test_send_import_onboarding_email_matches_welcome_credentials_copy(monkeypatch) -> None:
    sent: dict[str, str] = {}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: SimpleNamespace(login_url="https://valid8.example/login"),
    )

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
        system_name="VALID8",
    )

    assert sent["recipient_email"] == "imported.user@example.com"
    assert "Email: imported.user@example.com" in sent["body"]
    assert "Temporary Password: ImportPass123!" in sent["body"]
    assert "Login URL: https://valid8.example/login" in sent["body"]
    assert "Forgot Password option" not in sent["body"]
    assert "Login Credentials" in sent["html_body"]


def test_validate_email_delivery_settings_accepts_gmail_api_transport() -> None:
    resolved = email_service.validate_email_delivery_settings(
        _gmail_api_settings(),
    )

    assert resolved.transport == "gmail_api"
    assert resolved.auth_mode == "oauth2"
    assert resolved.sender_email == "mailer@example.com"
    assert resolved.from_email == "mailer@example.com"


def test_validate_email_delivery_settings_falls_back_to_authenticated_personal_gmail_sender() -> None:
    resolved = email_service.validate_email_delivery_settings(
        _gmail_api_settings(
            email_sender_email="person@gmail.com",
            email_from_email="no-reply@example.com",
            email_google_account_type="personal",
        )
    )

    assert resolved.from_email == "person@gmail.com"
    assert resolved.warnings


def test_validate_email_delivery_settings_rejects_workspace_custom_sender_without_opt_in() -> None:
    try:
        email_service.validate_email_delivery_settings(
            _gmail_api_settings(
                email_sender_email="mailer@school.edu",
                email_from_email="no-reply@school.edu",
                email_google_account_type="workspace",
                email_google_allow_custom_from=False,
            )
        )
    except email_service.EmailConfigurationError as exc:
        assert "EMAIL_GOOGLE_ALLOW_CUSTOM_FROM=true" in str(exc)
    else:
        raise AssertionError("Expected EmailConfigurationError for an unapproved Workspace sender")


def test_check_email_delivery_connection_verifies_gmail_api_custom_sender(monkeypatch) -> None:
    calls: list[str] = []

    class FakeResponse:
        def __init__(self, status_code: int, payload: dict[str, object]):
            self.status_code = status_code
            self._payload = payload
            self.text = json.dumps(payload)
            self.reason_phrase = "OK"

        def json(self):
            return self._payload

    settings = _gmail_api_settings(
        email_sender_email="mailer@school.edu",
        email_from_email="no-reply@school.edu",
        email_google_account_type="workspace",
        email_google_allow_custom_from=True,
    )

    monkeypatch.setattr(
        "app.services.email_service.transport._request_google_oauth_access_token",
        lambda settings: "access-token",
    )

    def fake_get(url: str, headers=None, timeout=None):
        calls.append(url)
        return FakeResponse(
            200,
            {"sendAsEmail": "no-reply@school.edu", "isPrimary": False, "verificationStatus": "accepted"},
        )

    monkeypatch.setattr(email_service.httpx, "get", fake_get)

    status = email_service.check_email_delivery_connection(settings=settings)

    assert status.transport == "gmail_api"
    assert status.host == "gmail.googleapis.com"
    assert calls


def test_send_plain_email_uses_gmail_api_transport(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        status_code = 200
        reason_phrase = "OK"
        text = ""

        def json(self):
            return {"id": "message-id"}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: _gmail_api_settings(),
    )
    monkeypatch.setattr(
        "app.services.email_service.transport._request_google_oauth_access_token",
        lambda settings: "access-token",
    )

    def fake_post(url: str, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(email_service.httpx, "post", fake_post)

    email_service.send_plain_email(
        recipient_email="recipient@example.com",
        subject="Subject",
        body="Body",
    )

    assert captured["url"] == "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    assert captured["headers"]["Authorization"] == "Bearer access-token"
    assert isinstance(captured["json"]["raw"], str)


def test_send_plain_email_surfaces_gmail_api_scope_errors(monkeypatch) -> None:
    class FakeResponse:
        status_code = 403
        reason_phrase = "Forbidden"
        text = json.dumps({"error": {"status": "PERMISSION_DENIED", "message": "Request had insufficient authentication scopes."}})

        def json(self):
            return {"error": {"status": "PERMISSION_DENIED", "message": "Request had insufficient authentication scopes."}}

    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: _gmail_api_settings(),
    )
    monkeypatch.setattr(
        "app.services.email_service.transport._request_google_oauth_access_token",
        lambda settings: "access-token",
    )
    monkeypatch.setattr(email_service.httpx, "post", lambda *args, **kwargs: FakeResponse())

    try:
        email_service.send_plain_email(
            recipient_email="recipient@example.com",
            subject="Subject",
            body="Body",
        )
    except email_service.EmailDeliveryError as exc:
        assert "gmail.send" in str(exc)
    else:
        raise AssertionError("Expected EmailDeliveryError for Gmail API scope failure")

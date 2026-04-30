from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.google_auth_service import (
    GoogleAuthDisabledError,
    GoogleAuthInvalidTokenError,
    GoogleEmailNotVerifiedError,
    verify_google_id_token,
)


def _settings(*, enabled=True, web="web-id", android="android-id"):
    return SimpleNamespace(
        google_login_enabled=enabled,
        google_web_client_id=web,
        google_android_client_id=android,
    )


def test_returns_payload_for_web_audience():
    payload = {
        "aud": "web-id",
        "iss": "accounts.google.com",
        "email": "USER@Example.com",
        "email_verified": True,
        "sub": "1234",
    }
    with patch("app.services.google_auth_service.id_token.verify_oauth2_token", return_value=payload):
        result = verify_google_id_token("token", settings=_settings())
    assert result["email"] == "user@example.com"
    assert result["sub"] == "1234"


def test_returns_payload_for_android_audience():
    payload = {
        "aud": "android-id",
        "iss": "https://accounts.google.com",
        "email": "user@example.com",
        "email_verified": True,
        "sub": "9",
    }
    with patch("app.services.google_auth_service.id_token.verify_oauth2_token", return_value=payload):
        result = verify_google_id_token("token", settings=_settings())
    assert result["email"] == "user@example.com"


def test_raises_when_disabled():
    with pytest.raises(GoogleAuthDisabledError):
        verify_google_id_token("token", settings=_settings(enabled=False))


def test_raises_when_no_client_ids_configured():
    with pytest.raises(GoogleAuthDisabledError):
        verify_google_id_token("token", settings=_settings(web="", android=""))


def test_raises_invalid_token_when_audience_mismatches():
    payload = {"aud": "other", "iss": "accounts.google.com", "email": "u@x", "email_verified": True}
    with patch("app.services.google_auth_service.id_token.verify_oauth2_token", return_value=payload):
        with pytest.raises(GoogleAuthInvalidTokenError):
            verify_google_id_token("token", settings=_settings())


def test_raises_invalid_token_when_issuer_mismatches():
    payload = {"aud": "web-id", "iss": "evil.example", "email": "u@x", "email_verified": True}
    with patch("app.services.google_auth_service.id_token.verify_oauth2_token", return_value=payload):
        with pytest.raises(GoogleAuthInvalidTokenError):
            verify_google_id_token("token", settings=_settings())


def test_raises_email_not_verified():
    payload = {"aud": "web-id", "iss": "accounts.google.com", "email": "u@x", "email_verified": False}
    with patch("app.services.google_auth_service.id_token.verify_oauth2_token", return_value=payload):
        with pytest.raises(GoogleEmailNotVerifiedError):
            verify_google_id_token("token", settings=_settings())


def test_raises_invalid_token_when_google_lib_raises():
    with patch(
        "app.services.google_auth_service.id_token.verify_oauth2_token",
        side_effect=ValueError("bad token"),
    ):
        with pytest.raises(GoogleAuthInvalidTokenError):
            verify_google_id_token("token", settings=_settings())

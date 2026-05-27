"""Use: Verifies Google ID tokens for the /auth/google endpoint.
Where to use: Called by the auth router when a frontend sends a Google id_token.
Role: Service layer. Encapsulates google-auth verification and policy checks.
"""

from __future__ import annotations

from typing import Any

import httpx
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import Settings, get_settings


_ALLOWED_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class GoogleAuthError(Exception):
    """Base class for Google auth domain errors."""


class GoogleAuthDisabledError(GoogleAuthError):
    """Raised when Google login is disabled or unconfigured."""


class GoogleAuthInvalidTokenError(GoogleAuthError):
    """Raised when the ID token cannot be validated."""


class GoogleEmailNotVerifiedError(GoogleAuthError):
    """Raised when the Google account email is not verified."""


def _allowed_audiences(settings: Settings) -> list[str]:
    return [c for c in (settings.google_web_client_id, settings.google_android_client_id) if c]


def verify_google_id_token(
    token: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    if not settings.google_login_enabled:
        raise GoogleAuthDisabledError("Google login is disabled.")

    audiences = _allowed_audiences(settings)
    if not audiences:
        raise GoogleAuthDisabledError("Google login is disabled.")

    try:
        payload = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=audiences,
        )
    except ValueError as exc:
        raise GoogleAuthInvalidTokenError(str(exc)) from exc

    if payload.get("aud") not in audiences:
        raise GoogleAuthInvalidTokenError("Token audience is not allowed.")

    if payload.get("iss") not in _ALLOWED_ISSUERS:
        raise GoogleAuthInvalidTokenError("Token issuer is not allowed.")

    if not payload.get("email_verified"):
        raise GoogleEmailNotVerifiedError("Google email is not verified.")

    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise GoogleAuthInvalidTokenError("Token has no email claim.")
    payload["email"] = email
    return payload


_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def verify_google_access_token(
    access_token: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Verify a Google OAuth2 access token by calling the userinfo endpoint.
    Used for web clients that receive an access_token instead of an id_token.
    """
    settings = settings or get_settings()
    if not settings.google_login_enabled:
        raise GoogleAuthDisabledError("Google login is disabled.")

    audiences = _allowed_audiences(settings)
    if not audiences:
        raise GoogleAuthDisabledError("Google login is disabled.")

    try:
        resp = httpx.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPStatusError as exc:
        raise GoogleAuthInvalidTokenError(f"Google userinfo returned {exc.response.status_code}.") from exc
    except Exception as exc:
        raise GoogleAuthInvalidTokenError(f"Failed to verify access token: {exc}") from exc

    if not payload.get("email_verified"):
        raise GoogleEmailNotVerifiedError("Google email is not verified.")

    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise GoogleAuthInvalidTokenError("Token has no email claim.")
    payload["email"] = email
    return payload

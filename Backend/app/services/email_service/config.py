"""Configuration helpers for the Gmail API email service package."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from email.utils import formataddr
from typing import Any

from email_validator import EmailNotValidError, validate_email as validate_email_address

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


# ======================================================
# CONSTANTS
# ======================================================

DEFAULT_SENDER_EMAIL = "noreply-aura@gmail.com"
DEFAULT_FROM_NAME = "Aura System"

GOOGLE_GMAIL_API_HOST = "https://gmail.googleapis.com"
ALLOWED_EMAIL_TRANSPORTS = {"disabled", "gmail_api"}
ALLOWED_GOOGLE_ACCOUNT_TYPES = {"auto", "personal", "workspace", "unknown"}
TEMPORARY_GMAIL_API_STATUS_CODES = {429, 500, 502, 503, 504}


# ======================================================
# EXCEPTIONS
# ======================================================

class EmailDeliveryError(Exception):
    pass


class EmailConfigurationError(EmailDeliveryError):
    pass


# ======================================================
# DATA CLASSES
# ======================================================

@dataclass(frozen=True)
class ResolvedEmailDeliverySettings:
    transport: str
    auth_mode: str
    sender_email: str
    from_email: str
    from_header: str
    reply_to: str | None
    google_account_type: str
    access_token: str = ""
    max_retries: int = 3
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "transport": self.transport,
            "auth_mode": self.auth_mode,
            "sender_email": self.sender_email,
            "from_email": self.from_email,
            "from_header": self.from_header,
            "reply_to": self.reply_to,
            "google_account_type": self.google_account_type,
            "access_token": "***" if self.access_token else "",
            "max_retries": self.max_retries,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class EmailConnectionStatus:
    is_connected: bool
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.is_connected


# ======================================================
# NORMALIZATION FUNCTIONS
# ======================================================

def _normalize_choice(value: str, allowed: set[str], field_name: str) -> str:
    normalized = (value or "").strip().lower()

    if normalized not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise EmailConfigurationError(
            f"{field_name} must be one of: {allowed_values}"
        )

    return normalized


def _normalize_email(
    value: str | None,
    field_name: str,
    *,
    allow_blank: bool = False,
) -> str:
    candidate = (value or "").strip()

    if not candidate:
        return DEFAULT_SENDER_EMAIL

    try:
        return validate_email_address(
            candidate,
            check_deliverability=False,
        ).normalized

    except EmailNotValidError as exc:
        raise EmailConfigurationError(
            f"{field_name} is not a valid email address: {exc}"
        ) from exc


def _normalize_runtime_email(value: str | None, field_name: str) -> str:
    try:
        return validate_email_address(
            (value or "").strip(),
            check_deliverability=False,
        ).normalized

    except EmailNotValidError as exc:
        raise EmailDeliveryError(
            f"{field_name} is not a valid email address: {exc}"
        ) from exc


# ======================================================
# GOOGLE CONFIG
# ======================================================

def _resolve_google_account_type(settings: Settings) -> str:
    configured = _normalize_choice(
        settings.email_google_account_type or "auto",
        ALLOWED_GOOGLE_ACCOUNT_TYPES,
        "EMAIL_GOOGLE_ACCOUNT_TYPE",
    )

    if configured != "auto":
        return configured

    normalized_sender = (
        settings.email_sender_email or DEFAULT_SENDER_EMAIL
    ).strip().lower()

    return "personal" if normalized_sender.endswith("@gmail.com") else "workspace"


# ======================================================
# SENDER SETTINGS
# ======================================================

def _resolve_sender_settings(
    settings: Settings,
    *,
    transport: str,
    google_account_type: str,
) -> ResolvedEmailDeliverySettings:
    normalized_sender_email = _normalize_email(
        settings.email_sender_email or DEFAULT_SENDER_EMAIL,
        "EMAIL_SENDER_EMAIL",
    )

    normalized_from_email = _normalize_email(
        settings.email_from_email or DEFAULT_SENDER_EMAIL,
        "EMAIL_FROM_EMAIL",
        allow_blank=True,
    )

    reply_to = _normalize_email(
        settings.email_reply_to or DEFAULT_SENDER_EMAIL,
        "EMAIL_REPLY_TO",
        allow_blank=True,
    )

    from_name = (settings.email_from_name or DEFAULT_FROM_NAME).strip()
    from_header = formataddr((from_name, normalized_from_email))

    access_token = (
        getattr(settings, "email_google_access_token", None) or ""
    ).strip()

    if not access_token:
        logger.warning(
            "EMAIL_GOOGLE_ACCESS_TOKEN is not set. "
            "Gmail API calls will fail until a valid token is provided."
        )

    max_retries = int(getattr(settings, "email_max_retries", None) or 3)

    return ResolvedEmailDeliverySettings(
        transport=transport,
        auth_mode="oauth2",
        sender_email=normalized_sender_email,
        from_email=normalized_from_email,
        from_header=from_header,
        reply_to=reply_to,
        google_account_type=google_account_type,
        access_token=access_token,
        max_retries=max_retries,
        warnings=(),
    )


# ======================================================
# MAIN VALIDATOR
# ======================================================

def validate_email_delivery_settings(
    settings: Settings | None = None,
) -> ResolvedEmailDeliverySettings:
    resolved_settings = settings or get_settings()

    transport = _normalize_choice(
        resolved_settings.email_transport or "gmail_api",
        ALLOWED_EMAIL_TRANSPORTS,
        "EMAIL_TRANSPORT",
    )

    if transport == "disabled":
        raise EmailConfigurationError(
            "EMAIL_TRANSPORT is disabled. Set it to 'gmail_api' to enable email delivery."
        )

    google_account_type = _resolve_google_account_type(resolved_settings)

    return _resolve_sender_settings(
        resolved_settings,
        transport=transport,
        google_account_type=google_account_type,
    )


# ======================================================
# STARTUP VALIDATION
# ======================================================

def validate_email_delivery_on_startup() -> None:
    from app.services.email_service.transport import check_email_delivery_connection

    app_settings = get_settings()

    try:
        resolved = validate_email_delivery_settings(app_settings)
    except EmailConfigurationError as exc:
        logger.error("Email service misconfigured: %s", exc)
        raise

    logger.info(
        "Email service configured | transport=%s sender=%s",
        resolved.transport,
        resolved.sender_email,
    )

    connection = check_email_delivery_connection(settings=resolved)

    if connection.ok:
        logger.info("Email connection verified successfully.")
    else:
        logger.warning(
            "Email connection check failed: %s — "
            "check EMAIL_GOOGLE_ACCESS_TOKEN in your .env file.",
            connection.error or "unknown error",
        )
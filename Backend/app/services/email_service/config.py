"""Configuration helpers for the Mailjet-backed email service."""

from __future__ import annotations

from dataclasses import dataclass
from email.utils import formataddr
from urllib.parse import urlparse

from email_validator import EmailNotValidError, validate_email as validate_email_address

from app.core.config import Settings

MAILJET_API_HOST = "api.mailjet.com"
ALLOWED_EMAIL_TRANSPORTS = {"disabled", "mailjet_api"}
TEMPORARY_MAILJET_STATUS_CODES = {429, 500, 502, 503, 504}


class EmailDeliveryError(Exception):
    pass


class EmailConfigurationError(EmailDeliveryError):
    pass


@dataclass(frozen=True)
class ResolvedEmailDeliverySettings:
    transport: str
    auth_mode: str
    sender_email: str
    sender_name: str
    from_header: str
    reply_to: str | None
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class EmailConnectionStatus:
    host: str
    port: int
    transport: str
    auth_mode: str
    sender: str
    reply_to: str | None
    warnings: tuple[str, ...]


def _normalize_choice(value: str, allowed: set[str], field_name: str) -> str:
    normalized = value.strip().lower()
    if normalized not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise EmailConfigurationError(f"{field_name} must be one of: {allowed_values}")
    return normalized


def _normalize_email(value: str | None, field_name: str, *, allow_blank: bool = False) -> str:
    candidate = (value or "").strip()
    if not candidate:
        if allow_blank:
            return ""
        raise EmailConfigurationError(f"{field_name} is not configured")

    try:
        return validate_email_address(candidate, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise EmailConfigurationError(f"{field_name} is not a valid email address: {exc}") from exc


def _normalize_runtime_email(value: str | None, field_name: str) -> str:
    try:
        return validate_email_address((value or "").strip(), check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise EmailDeliveryError(f"{field_name} is not a valid email address: {exc}") from exc


def _mailjet_api_host(settings: Settings) -> str:
    parsed = urlparse(settings.mailjet_api_base_url)
    return parsed.netloc or MAILJET_API_HOST


def _resolve_sender_settings(settings: Settings, *, transport: str) -> ResolvedEmailDeliverySettings:
    normalized_sender_email = _normalize_email(settings.email_sender_email, "EMAIL_SENDER_EMAIL")
    sender_name = (settings.email_sender_name or "").strip()
    if not sender_name:
        raise EmailConfigurationError("EMAIL_SENDER_NAME is not configured")

    reply_to = _normalize_email(
        settings.email_reply_to,
        "EMAIL_REPLY_TO",
        allow_blank=True,
    ) or None

    return ResolvedEmailDeliverySettings(
        transport=transport,
        auth_mode="basic",
        sender_email=normalized_sender_email,
        sender_name=sender_name,
        from_header=formataddr((sender_name, normalized_sender_email)),
        reply_to=reply_to,
        warnings=(),
    )


def validate_email_delivery_settings(settings: Settings | None = None) -> ResolvedEmailDeliverySettings:
    from . import get_settings

    resolved_settings = settings or get_settings()
    transport = _normalize_choice(
        resolved_settings.email_transport or "disabled",
        ALLOWED_EMAIL_TRANSPORTS,
        "EMAIL_TRANSPORT",
    )

    if transport == "disabled":
        raise EmailConfigurationError(
            "EMAIL_TRANSPORT is disabled. Set EMAIL_TRANSPORT to mailjet_api to enable outbound email delivery."
        )

    if resolved_settings.email_timeout_seconds <= 0:
        raise EmailConfigurationError("Email timeout must be greater than 0.")

    if transport == "mailjet_api":
        missing_fields = [
            field_name
            for field_name, value in [
                ("EMAIL_SENDER_EMAIL", resolved_settings.email_sender_email),
                ("EMAIL_SENDER_NAME", resolved_settings.email_sender_name),
                ("MAILJET_API_KEY", resolved_settings.mailjet_api_key),
                ("MAILJET_API_SECRET", resolved_settings.mailjet_api_secret),
            ]
            if not (value or "").strip()
        ]
        if missing_fields:
            raise EmailConfigurationError(
                "Missing Mailjet settings: " + ", ".join(missing_fields)
            )
        if not resolved_settings.mailjet_api_base_url.strip():
            raise EmailConfigurationError("Mailjet API base URL is not configured.")

        return _resolve_sender_settings(
            resolved_settings,
            transport=transport,
        )

    raise EmailConfigurationError(f"Unsupported EMAIL_TRANSPORT value: {transport}")


def validate_email_delivery_on_startup() -> None:
    from . import (
        check_email_delivery_connection,
        get_email_delivery_summary,
        get_settings,
        logger,
    )

    settings = get_settings()
    transport = _normalize_choice(
        settings.email_transport or "disabled",
        ALLOWED_EMAIL_TRANSPORTS,
        "EMAIL_TRANSPORT",
    )

    if transport == "disabled":
        logger.warning(
            "Outbound email delivery is disabled. Forgot-password and onboarding emails will not be sent."
        )
        return

    resolved_delivery = validate_email_delivery_settings(settings)
    for warning in resolved_delivery.warnings:
        logger.warning(warning)

    summary = get_email_delivery_summary(settings)
    logger.info(
        "Email delivery configured: transport=%s host=%s port=%s sender=%s",
        summary["transport"],
        summary["host"],
        summary["port"],
        summary["sender"],
    )

    if settings.email_verify_connection_on_startup:
        check_email_delivery_connection(settings=settings)
        logger.info("Email delivery connection verified during startup.")

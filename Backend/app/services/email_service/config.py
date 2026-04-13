"""Configuration helpers for the email service package."""

from __future__ import annotations

from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email as validate_email_address

from app.core.config import Settings

GOOGLE_GMAIL_API_HOST = "gmail.googleapis.com"
ALLOWED_EMAIL_TRANSPORTS = {"disabled", "gmail_api", "smtp"}
ALLOWED_GOOGLE_ACCOUNT_TYPES = {"auto", "personal", "workspace", "unknown"}
TEMPORARY_GMAIL_API_STATUS_CODES = {429, 500, 502, 503, 504}


class EmailDeliveryError(Exception):
    pass


class EmailConfigurationError(EmailDeliveryError):
    pass


@dataclass(frozen=True)
class ResolvedEmailDeliverySettings:
    transport: str
    auth_mode: str
    sender_email: str
    from_email: str
    from_header: str
    reply_to: str | None
    google_account_type: str
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


def _gmail_api_host(settings: Settings) -> str:
    from urllib.parse import urlparse

    parsed = urlparse(settings.google_gmail_api_base_url)
    return parsed.netloc or GOOGLE_GMAIL_API_HOST


def _resolve_google_account_type(settings: Settings) -> str:
    configured = _normalize_choice(
        settings.email_google_account_type or "auto",
        ALLOWED_GOOGLE_ACCOUNT_TYPES,
        "EMAIL_GOOGLE_ACCOUNT_TYPE",
    )
    if configured != "auto":
        return configured

    normalized_sender = (settings.email_sender_email or "").strip().lower()
    if normalized_sender.endswith("@gmail.com") or normalized_sender.endswith("@googlemail.com"):
        return "personal"
    if normalized_sender:
        return "workspace"
    return "unknown"


def _resolve_sender_settings(
    settings: Settings,
    *,
    transport: str,
    google_account_type: str,
    auth_mode: str,
    enforce_google_alias_rules: bool,
) -> ResolvedEmailDeliverySettings:
    from email.utils import formataddr

    normalized_sender_email = _normalize_email(settings.email_sender_email, "EMAIL_SENDER_EMAIL")
    normalized_from_email = _normalize_email(
        settings.email_from_email,
        "EMAIL_FROM_EMAIL",
        allow_blank=True,
    )
    reply_to = _normalize_email(
        settings.email_reply_to,
        "EMAIL_REPLY_TO",
        allow_blank=True,
    ) or None
    warnings: list[str] = []

    if not normalized_from_email:
        normalized_from_email = normalized_sender_email

    if enforce_google_alias_rules:
        if google_account_type == "personal" and normalized_from_email != normalized_sender_email:
            warnings.append(
                "EMAIL_FROM_EMAIL was changed to the authenticated Gmail address because personal "
                "Gmail cannot reliably send as an arbitrary custom-domain sender."
            )
            normalized_from_email = normalized_sender_email
        elif (
            normalized_from_email != normalized_sender_email
            and not settings.email_google_allow_custom_from
        ):
            raise EmailConfigurationError(
                "EMAIL_FROM_EMAIL differs from EMAIL_SENDER_EMAIL. For Google Workspace aliases or "
                "Gmail 'Send mail as' aliases, configure the alias in Google first and then set "
                "EMAIL_GOOGLE_ALLOW_CUSTOM_FROM=true. Otherwise use the authenticated mailbox as the sender."
            )

    from_name = (settings.email_from_name or "").strip()
    from_header = formataddr((from_name, normalized_from_email)) if from_name else normalized_from_email

    return ResolvedEmailDeliverySettings(
        transport=transport,
        auth_mode=auth_mode,
        sender_email=normalized_sender_email,
        from_email=normalized_from_email,
        from_header=from_header,
        reply_to=reply_to,
        google_account_type=google_account_type,
        warnings=tuple(warnings),
    )


def _validate_smtp_transport_settings(settings: Settings) -> None:
    if not (settings.smtp_host or "").strip():
        raise EmailConfigurationError("SMTP_HOST is not configured")
    if int(settings.smtp_port) <= 0:
        raise EmailConfigurationError("SMTP_PORT must be greater than 0")
    if settings.smtp_use_tls and settings.smtp_use_starttls:
        raise EmailConfigurationError("SMTP_USE_TLS and SMTP_USE_STARTTLS cannot both be true")
    if settings.smtp_username and not settings.smtp_password:
        raise EmailConfigurationError("SMTP_PASSWORD is required when SMTP_USERNAME is configured")


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
            "EMAIL_TRANSPORT is disabled. Set EMAIL_TRANSPORT to smtp or gmail_api to enable outbound email delivery."
        )

    if resolved_settings.email_timeout_seconds <= 0:
        raise EmailConfigurationError("EMAIL_TIMEOUT_SECONDS must be greater than 0")

    if transport == "gmail_api":
        if not resolved_settings.google_gmail_api_base_url.strip():
            raise EmailConfigurationError("GOOGLE_GMAIL_API_BASE_URL is not configured")

        missing_oauth_fields = [
            field_name
            for field_name, value in [
                ("EMAIL_SENDER_EMAIL", resolved_settings.email_sender_email),
                ("GOOGLE_OAUTH_CLIENT_ID", resolved_settings.google_oauth_client_id),
                ("GOOGLE_OAUTH_CLIENT_SECRET", resolved_settings.google_oauth_client_secret),
                ("GOOGLE_OAUTH_REFRESH_TOKEN", resolved_settings.google_oauth_refresh_token),
                ("GOOGLE_OAUTH_TOKEN_URL", resolved_settings.google_oauth_token_url),
            ]
            if not value
        ]
        if missing_oauth_fields:
            raise EmailConfigurationError(
                "Missing Gmail API settings: " + ", ".join(missing_oauth_fields)
            )

        google_account_type = _resolve_google_account_type(resolved_settings)
        return _resolve_sender_settings(
            resolved_settings,
            transport=transport,
            google_account_type=google_account_type,
            auth_mode="oauth2",
            enforce_google_alias_rules=True,
        )

    if transport == "smtp":
        _validate_smtp_transport_settings(resolved_settings)
        return _resolve_sender_settings(
            resolved_settings,
            transport=transport,
            google_account_type="unknown",
            auth_mode="plain" if resolved_settings.smtp_username else "none",
            enforce_google_alias_rules=False,
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
        if settings.email_required_on_startup:
            raise EmailConfigurationError(
                "EMAIL_REQUIRED_ON_STARTUP is enabled but EMAIL_TRANSPORT is disabled."
            )
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

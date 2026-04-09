"""
app/services/email_service/__init__.py
---------------------------------------
Public interface for the Aura email service.

Package layout
--------------
  config      — constants, enums, error types, settings validation, startup probe
  rendering   — Jinja/HTML template builders for each email use case
  transport   — low-level Gmail API header builder, MIME construction, send + retry
  use_cases   — high-level orchestrators that combine rendering + transport

Import from this package directly in routers, workers, and other services:

    from app.services.email_service import send_welcome_email
    from app.services.email_service import check_email_delivery_connection

Do NOT import from the sub-modules directly — that is an implementation detail
and may change without notice.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings

# ======================================================
# CONFIG
# ======================================================

from .config import (
    ALLOWED_EMAIL_TRANSPORTS,
    ALLOWED_GOOGLE_ACCOUNT_TYPES,
    GOOGLE_GMAIL_API_HOST,
    TEMPORARY_GMAIL_API_STATUS_CODES,
    EmailConfigurationError,
    EmailConnectionStatus,
    EmailDeliveryError,
    ResolvedEmailDeliverySettings,
    validate_email_delivery_on_startup,
    validate_email_delivery_settings,
)

# ======================================================
# RENDERING
# ======================================================

from .rendering import (
    _send_email,
    build_import_onboarding_email_content,
    build_mfa_code_email_content,
    build_password_reset_email_content,
    build_welcome_email_content,
)

# ======================================================
# TRANSPORT
# ======================================================

from .transport import (
    build_gmail_api_headers,
    check_email_delivery_connection,
    get_email_delivery_summary,
    httpx,
    send_plain_email,
    send_test_email,
    send_transactional_email,
)

# ======================================================
# USE CASES
# ======================================================

from .use_cases import (
    send_import_onboarding_email,
    send_mfa_code_email,
    send_password_reset_email,
    send_welcome_email,
)

# ======================================================
# EXPORTS
# ======================================================

logger = logging.getLogger(__name__)

__all__ = [
    # --- config ---
    "ALLOWED_EMAIL_TRANSPORTS",
    "ALLOWED_GOOGLE_ACCOUNT_TYPES",
    "GOOGLE_GMAIL_API_HOST",
    "TEMPORARY_GMAIL_API_STATUS_CODES",
    "EmailConfigurationError",
    "EmailConnectionStatus",
    "EmailDeliveryError",
    "ResolvedEmailDeliverySettings",
    "get_settings",
    "validate_email_delivery_on_startup",
    "validate_email_delivery_settings",
    # --- rendering ---
    "build_import_onboarding_email_content",
    "build_mfa_code_email_content",
    "build_password_reset_email_content",
    "build_welcome_email_content",
    # --- transport ---
    "build_gmail_api_headers",
    "check_email_delivery_connection",
    "get_email_delivery_summary",
    "httpx",
    "send_plain_email",
    "send_test_email",
    "send_transactional_email",
    # --- use cases ---
    "send_import_onboarding_email",
    "send_mfa_code_email",
    "send_password_reset_email",
    "send_welcome_email",
]

"""Mailjet-backed email service package."""

from __future__ import annotations

import httpx
import logging

from app.core.config import Settings, get_settings
from app.services.password_change_policy import get_welcome_email_password_notice

from .config import (
    ALLOWED_EMAIL_TRANSPORTS,
    MAILJET_API_HOST,
    TEMPORARY_MAILJET_STATUS_CODES,
    EmailConfigurationError,
    EmailConnectionStatus,
    EmailDeliveryError,
    ResolvedEmailDeliverySettings,
    validate_email_delivery_on_startup,
    validate_email_delivery_settings,
)
from .rendering import (
    _send_email,
    build_import_onboarding_email_content,
    build_password_reset_email_content,
    build_welcome_email_content,
)
from .transport import (
    _build_mailjet_payload,
    _build_message,
    _extract_mailjet_error_detail,
    _mailjet_rest_sender_url,
    _mailjet_timeout,
    check_email_delivery_connection,
    get_email_delivery_summary,
    send_plain_email,
    send_test_email,
    send_transactional_email,
)
from .use_cases import (
    send_import_onboarding_email,
    send_password_reset_email,
    send_welcome_email,
)

logger = logging.getLogger(__name__)

__all__ = [name for name in globals() if not name.startswith("__")]

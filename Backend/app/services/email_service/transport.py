"""
transport.py
------------
Low-level Gmail API transport layer.
Handles header construction, raw sending, connection checks, and delivery summaries.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from collections.abc import Mapping
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

from app.services.email_service.config import (
    GOOGLE_GMAIL_API_HOST,
    TEMPORARY_GMAIL_API_STATUS_CODES,
    EmailConnectionStatus,
    EmailConfigurationError,
    EmailDeliveryError,
    ResolvedEmailDeliverySettings,
    validate_email_delivery_settings,
)

logger = logging.getLogger(__name__)


def _get_runtime_settings():
    import app.services.email_service as email_service

    return email_service.get_settings()


def _request_google_oauth_access_token(settings) -> str:
    access_token = (getattr(settings, "email_google_access_token", "") or "").strip()
    if access_token:
        return access_token

    refresh_token = (getattr(settings, "google_oauth_refresh_token", "") or "").strip()
    client_id = (getattr(settings, "google_oauth_client_id", "") or "").strip()
    client_secret = (getattr(settings, "google_oauth_client_secret", "") or "").strip()
    token_url = (getattr(settings, "google_oauth_token_url", "") or "").strip()

    if not all([refresh_token, client_id, client_secret, token_url]):
        raise EmailConfigurationError(
            "Google OAuth email delivery requires GOOGLE_OAUTH_CLIENT_ID, "
            "GOOGLE_OAUTH_CLIENT_SECRET, GOOGLE_OAUTH_REFRESH_TOKEN, and GOOGLE_OAUTH_TOKEN_URL."
        )

    response = httpx.post(
        token_url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=float(getattr(settings, "email_timeout_seconds", 20) or 20),
    )
    try:
        payload = response.json()
    except Exception:
        payload = {}

    if response.status_code != 200:
        raise EmailDeliveryError(
            f"Failed to refresh Gmail API access token: {response.status_code} {response.text}"
        )

    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise EmailDeliveryError("Google OAuth token response did not include an access_token.")
    return token


def _describe_gmail_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        payload = {}

    error_payload = payload.get("error") if isinstance(payload, Mapping) else None
    if isinstance(error_payload, Mapping):
        message = str(error_payload.get("message") or "").strip()
        if "insufficient authentication scopes" in message.lower():
            return (
                "Gmail API rejected the request because the token is missing the "
                "gmail.send scope."
            )
        if message:
            return message

    return f"Gmail API returned {response.status_code}: {response.text}"


# ======================================================
# HEADER BUILDER
# ======================================================

def build_gmail_api_headers(access_token: str) -> dict[str, str]:
    """
    Build the HTTP headers required for authenticated Gmail API requests.

    Args:
        access_token: A valid OAuth2 bearer token for the Gmail API.

    Returns:
        A dict of headers ready to pass to an httpx/requests call.
    """
    if not access_token:
        raise ValueError("access_token must not be empty when building Gmail API headers.")

    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ======================================================
# MIME BUILDER
# ======================================================

def _build_mime_message(
    *,
    sender: str,
    recipient_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> str:
    """
    Construct and base64url-encode a MIME message for the Gmail API.

    Returns:
        A base64url-encoded raw message string.
    """
    message = MIMEMultipart("alternative")
    message["From"] = sender
    message["To"] = recipient_email
    message["Subject"] = subject

    message.attach(MIMEText(text_body, "plain", "utf-8"))
    if html_body:
        message.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return raw


# ======================================================
# CORE SEND
# ======================================================

def send_transactional_email(
    *,
    recipient_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    settings: ResolvedEmailDeliverySettings | None = None,
) -> None:
    """
    Send a transactional email via the Gmail API.

    Args:
        recipient_email: Destination email address.
        subject:         Email subject line.
        text_body:       Plain-text fallback body.
        html_body:       Optional HTML body (preferred by modern clients).
        settings:        Optional pre-resolved delivery settings; resolved
                         from app config when not supplied.

    Raises:
        EmailDeliveryError: On any permanent or unrecoverable send failure.
    """
    runtime_settings = _get_runtime_settings()
    if settings is None:
        settings = validate_email_delivery_settings(runtime_settings)
    elif not isinstance(settings, ResolvedEmailDeliverySettings):
        settings = validate_email_delivery_settings(settings)
    access_token = getattr(settings, "access_token", "") or _request_google_oauth_access_token(runtime_settings)

    raw_message = _build_mime_message(
        sender=settings.from_header,
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )

    payload = {"raw": raw_message}
    headers = build_gmail_api_headers(access_token)
    url = f"{GOOGLE_GMAIL_API_HOST}/gmail/v1/users/me/messages/send"

    last_exc: Exception | None = None
    for attempt in range(1, settings.max_retries + 1):
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=15.0)

            if response.status_code == 200:
                logger.info(
                    "Email sent successfully | to=%s subject=%r attempt=%d",
                    recipient_email,
                    subject,
                    attempt,
                )
                return

            if response.status_code in TEMPORARY_GMAIL_API_STATUS_CODES and attempt < settings.max_retries:
                wait = 2 ** attempt
                logger.warning(
                    "Transient Gmail API error %d — retrying in %ds (attempt %d/%d)",
                    response.status_code,
                    wait,
                    attempt,
                    settings.max_retries,
                )
                time.sleep(wait)
                last_exc = EmailDeliveryError(
                    f"Gmail API returned {response.status_code}: {response.text}"
                )
                continue

            # Permanent failure
            raise EmailDeliveryError(_describe_gmail_error(response))

        except httpx.TimeoutException as exc:
            last_exc = exc
            logger.warning("Gmail API timeout on attempt %d/%d", attempt, settings.max_retries)
            if attempt < settings.max_retries:
                time.sleep(2 ** attempt)
        except httpx.RequestError as exc:
            raise EmailDeliveryError(f"Network error while sending email: {exc}") from exc

    raise EmailDeliveryError(
        f"Failed to send email after {settings.max_retries} attempts."
    ) from last_exc


# ======================================================
# CONNECTION CHECK
# ======================================================

def check_email_delivery_connection(
    settings: ResolvedEmailDeliverySettings | None = None,
) -> EmailConnectionStatus:
    """
    Probe the Gmail API to verify the current credentials and connectivity.

    Returns:
        EmailConnectionStatus with is_connected and an optional error message.
    """
    try:
        runtime_settings = _get_runtime_settings()
        if settings is None:
            settings = validate_email_delivery_settings(runtime_settings)
        elif not isinstance(settings, ResolvedEmailDeliverySettings):
            settings = validate_email_delivery_settings(settings)

        access_token = getattr(settings, "access_token", "") or _request_google_oauth_access_token(runtime_settings)
        headers = build_gmail_api_headers(access_token)
        host = GOOGLE_GMAIL_API_HOST.replace("https://", "")
        if settings.from_email != settings.sender_email:
            url = f"{GOOGLE_GMAIL_API_HOST}/gmail/v1/users/me/settings/sendAs/{settings.from_email}"
        else:
            url = f"{GOOGLE_GMAIL_API_HOST}/gmail/v1/users/me/profile"

        response = httpx.get(url, headers=headers, timeout=10.0)

        if response.status_code == 200:
            payload = response.json()
            logger.info("Gmail API connection OK | account=%s", payload.get("emailAddress", settings.from_email))
            return EmailConnectionStatus(
                is_connected=True,
                transport=settings.transport,
                host=host,
            )

        return EmailConnectionStatus(
            is_connected=False,
            error=_describe_gmail_error(response),
            transport=settings.transport,
            host=host,
        )

    except Exception as exc:
        logger.exception("Email connection check failed")
        return EmailConnectionStatus(
            is_connected=False,
            error=str(exc),
            host=GOOGLE_GMAIL_API_HOST.replace("https://", ""),
        )


# ======================================================
# DELIVERY SUMMARY
# ======================================================

def get_email_delivery_summary(
    settings: ResolvedEmailDeliverySettings | None = None,
) -> dict[str, Any]:
    """
    Return a human-readable summary of the current email delivery configuration.

    Useful for health-check endpoints and admin dashboards.
    """
    try:
        if settings is None:
            settings = validate_email_delivery_settings(_get_runtime_settings())
        elif not isinstance(settings, ResolvedEmailDeliverySettings):
            settings = validate_email_delivery_settings(settings)

        connection = check_email_delivery_connection(settings)

        return {
            "transport": settings.transport,
            "sender_email": settings.sender_email,
            "account_type": settings.google_account_type,
            "is_connected": connection.is_connected,
            "error": connection.error,
            "max_retries": settings.max_retries,
        }

    except Exception as exc:
        logger.exception("Failed to build email delivery summary")
        return {
            "transport": "unknown",
            "sender_email": "unknown",
            "account_type": "unknown",
            "is_connected": False,
            "error": str(exc),
            "max_retries": 0,
        }


# ======================================================
# TEST EMAIL
# ======================================================

def send_test_email(
    *,
    recipient_email: str,
) -> None:
    """
    Send a diagnostic test email to verify the mailing system is operational.

    Args:
        recipient_email: Address to deliver the test message to.
    """
    send_transactional_email(
        recipient_email=recipient_email,
        subject="Aura System — Test Email",
        text_body=(
            "Hello,\n\n"
            "This is a test email from the Aura System.\n\n"
            "If you received this message, the mailing system is working correctly.\n\n"
            "Sender: noreply-aura@gmail.com\n\n"
            "Best regards,\n"
            "Aura System"
        ),
        html_body="""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Aura System Test Email</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="580" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:8px;overflow:hidden;
                      box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background:#4f46e5;padding:32px 40px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;
                         letter-spacing:0.5px;">Aura System</h1>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <h2 style="margin:0 0 16px;color:#1a1a2e;font-size:18px;">
                ✅ Test Email
              </h2>
              <p style="margin:0 0 12px;color:#444;font-size:15px;line-height:1.6;">
                Hello,
              </p>
              <p style="margin:0 0 12px;color:#444;font-size:15px;line-height:1.6;">
                This is a test email from the <strong>Aura System</strong>.
              </p>
              <p style="margin:0 0 24px;color:#444;font-size:15px;line-height:1.6;">
                If you received this message, the mailing system is
                <strong>working correctly</strong>.
              </p>
              <hr style="border:none;border-top:1px solid #e8e8e8;margin:24px 0;" />
              <p style="margin:0;color:#888;font-size:13px;">
                Sender: <a href="mailto:noreply-aura@gmail.com"
                           style="color:#4f46e5;text-decoration:none;">
                  noreply-aura@gmail.com
                </a>
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#f9f9f9;padding:20px 40px;text-align:center;">
              <p style="margin:0;color:#aaa;font-size:12px;">
                © 2024 Aura System · This is an automated message, please do not reply.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
        """,
    )


# ======================================================
# BACKWARD COMPATIBILITY
# ======================================================

def send_plain_email(
    *,
    recipient_email: str,
    subject: str,
    text_body: str | None = None,
    body: str | None = None,
    html_body: str | None = None,
) -> None:
    """
    Thin wrapper around send_transactional_email kept for backward compatibility.

    Prefer calling send_transactional_email directly in new code.
    """
    send_transactional_email(
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body if text_body is not None else (body or ""),
        html_body=html_body,
    )

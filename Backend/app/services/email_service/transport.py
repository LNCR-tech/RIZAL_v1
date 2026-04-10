"""Transport helpers for the Gmail API email service package."""

from __future__ import annotations

import base64
from urllib.parse import quote

from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from app.core.config import Settings

from .config import (
    TEMPORARY_GMAIL_API_STATUS_CODES,
    EmailConnectionStatus,
    EmailDeliveryError,
)


def _request_google_oauth_access_token(settings: Settings) -> str:
    from . import httpx

    try:
        response = httpx.post(
            settings.google_oauth_token_url,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "refresh_token": settings.google_oauth_refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=_gmail_api_timeout(settings),
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        body = exc.response.text.strip()
        detail = body[:300] if body else exc.response.reason_phrase
        if exc.response.status_code == 400 and "invalid_grant" in body.lower():
            raise EmailDeliveryError(
                "Google OAuth refresh token is invalid, expired, or revoked. "
                "Generate a new refresh token and update GOOGLE_OAUTH_REFRESH_TOKEN."
            ) from exc
        raise EmailDeliveryError(
            f"Failed to refresh the Google OAuth access token: {detail}"
        ) from exc
    except httpx.HTTPError as exc:
        raise EmailDeliveryError(
            "Could not reach the Google OAuth token endpoint. Check outbound network access and GOOGLE_OAUTH_TOKEN_URL."
        ) from exc

    access_token = response.json().get("access_token")
    if not access_token:
        raise EmailDeliveryError(
            "Google OAuth token response did not include an access_token."
        )
    return access_token


def _extract_google_api_error_detail(response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return (response.text or response.reason_phrase or "").strip()

    error_payload = payload.get("error")
    if isinstance(error_payload, dict):
        message = (error_payload.get("message") or "").strip()
        status = (error_payload.get("status") or "").strip()
        if message and status:
            return f"{status}: {message}"
        return message or status or (response.reason_phrase or "").strip()
    if isinstance(error_payload, str):
        return error_payload.strip()
    return (response.text or response.reason_phrase or "").strip()


def _build_gmail_api_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _gmail_api_timeout(settings: Settings) -> float:
    return float(settings.email_timeout_seconds)


def _verify_gmail_api_sender(
    *,
    settings: Settings,
    resolved_delivery,
    access_token: str,
) -> None:
    from . import httpx

    if resolved_delivery.from_email == resolved_delivery.sender_email:
        return

    send_as_url = (
        settings.google_gmail_api_base_url.rstrip("/")
        + "/users/me/settings/sendAs/"
        + quote(resolved_delivery.from_email, safe="@")
    )
    try:
        response = httpx.get(
            send_as_url,
            headers=_build_gmail_api_headers(access_token),
            timeout=_gmail_api_timeout(settings),
        )
    except httpx.HTTPError as exc:
        raise EmailDeliveryError(
            "Could not reach the Gmail API send-as settings endpoint. Check outbound HTTPS access."
        ) from exc

    detail = _extract_google_api_error_detail(response)
    if response.status_code == 200:
        send_as = response.json()
        is_primary = bool(send_as.get("isPrimary"))
        verification_status = (send_as.get("verificationStatus") or "").strip().lower()
        if is_primary or verification_status in {"accepted", "verified"}:
            return
        raise EmailDeliveryError(
            "Gmail API found the configured sender address, but it is not verified yet. "
            "Verify the send-as alias in Gmail settings before using it."
        )

    if response.status_code == 403 and "scope" in detail.lower():
        raise EmailDeliveryError(
            "The Google OAuth token cannot verify the configured custom sender because it lacks "
            "the Gmail settings scope. Reauthorize with "
            "https://www.googleapis.com/auth/gmail.settings.basic or use the authenticated mailbox as the sender."
        )

    if response.status_code == 404:
        raise EmailDeliveryError(
            "Gmail API does not recognize the configured sender address. "
            "Set EMAIL_FROM_EMAIL to the authenticated mailbox or configure this address as a verified Gmail send-as alias first."
        )

    if response.status_code in TEMPORARY_GMAIL_API_STATUS_CODES:
        raise EmailDeliveryError(f"Temporary Gmail API sender-verification failure: {detail}")

    raise EmailDeliveryError(f"Gmail API sender verification failed: {detail}")


def _encode_message_for_gmail_api(msg: EmailMessage) -> str:
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def _send_via_gmail_api(
    *,
    settings: Settings,
    resolved_delivery,
    msg: EmailMessage,
) -> None:
    from . import httpx

    access_token = _request_google_oauth_access_token(settings)
    send_url = settings.google_gmail_api_base_url.rstrip("/") + "/users/me/messages/send"
    payload = {"raw": _encode_message_for_gmail_api(msg)}

    try:
        response = httpx.post(
            send_url,
            headers=_build_gmail_api_headers(access_token),
            json=payload,
            timeout=_gmail_api_timeout(settings),
        )
    except httpx.TimeoutException as exc:
        raise EmailDeliveryError(
            "Timed out while calling the Gmail API. Check outbound HTTPS access from the deployment host."
        ) from exc
    except httpx.HTTPError as exc:
        raise EmailDeliveryError(
            "Could not reach the Gmail API send endpoint. Check outbound HTTPS access from the deployment host."
        ) from exc

    if response.status_code == 200:
        return

    detail = _extract_google_api_error_detail(response)
    detail_lower = detail.lower()
    if response.status_code == 400 and (
        "from header" in detail_lower
        or "invalid argument" in detail_lower
        or "bad request" in detail_lower
    ):
        raise EmailDeliveryError(
            "Gmail API rejected the configured sender address. "
            "Use the authenticated mailbox as EMAIL_FROM_EMAIL or configure the custom sender as a verified Gmail send-as alias."
        )
    if response.status_code == 401:
        raise EmailDeliveryError(
            "Google OAuth access token was rejected by the Gmail API. Reauthorize and update the refresh token."
        )
    if response.status_code == 403:
        if "insufficient permission" in detail_lower or "scope" in detail_lower:
            raise EmailDeliveryError(
                "The Google OAuth token does not include the required Gmail API permissions. "
                "Reauthorize with https://www.googleapis.com/auth/gmail.send."
            )
        raise EmailDeliveryError(f"Gmail API request was forbidden: {detail}")
    if response.status_code in TEMPORARY_GMAIL_API_STATUS_CODES:
        raise EmailDeliveryError(
            f"Temporary Gmail API failure ({response.status_code}). Retry later: {detail}"
        )
    raise EmailDeliveryError(
        f"Gmail API send failed with status {response.status_code}: {detail or response.reason_phrase}"
    )


def _build_message(
    *,
    resolved_delivery,
    recipient_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    reply_to: str | None = None,
) -> EmailMessage:
    from .config import _normalize_runtime_email

    recipient = _normalize_runtime_email(recipient_email, "recipient_email")
    effective_reply_to = (
        _normalize_runtime_email(reply_to, "reply_to")
        if reply_to is not None
        else resolved_delivery.reply_to
    )
    if not subject.strip():
        raise EmailDeliveryError("Email subject cannot be blank.")
    if not text_body.strip():
        raise EmailDeliveryError("Email body cannot be blank.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = resolved_delivery.from_header
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=resolved_delivery.from_email.split("@", 1)[-1])
    if effective_reply_to:
        msg["Reply-To"] = effective_reply_to
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    return msg


def send_transactional_email(
    *,
    recipient_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    reply_to: str | None = None,
) -> None:
    from . import (
        get_settings,
        logger,
        validate_email_delivery_settings,
    )

    settings = get_settings()
    resolved_delivery = validate_email_delivery_settings(settings)

    for warning in resolved_delivery.warnings:
        logger.warning(warning)

    msg = _build_message(
        resolved_delivery=resolved_delivery,
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        reply_to=reply_to,
    )

    _send_via_gmail_api(
        settings=settings,
        resolved_delivery=resolved_delivery,
        msg=msg,
    )


def send_plain_email(
    *,
    recipient_email: str,
    subject: str,
    body: str,
) -> None:
    send_transactional_email(
        recipient_email=recipient_email,
        subject=subject,
        text_body=body,
    )


def check_email_delivery_connection(
    *,
    settings: Settings | None = None,
    verify_sender: bool = True,
) -> EmailConnectionStatus:
    from . import (
        get_settings,
        logger,
        validate_email_delivery_settings,
    )
    from .config import _gmail_api_host

    resolved_settings = settings or get_settings()
    resolved_delivery = validate_email_delivery_settings(resolved_settings)

    for warning in resolved_delivery.warnings:
        logger.warning(warning)

    access_token = _request_google_oauth_access_token(resolved_settings)
    if verify_sender:
        _verify_gmail_api_sender(
            settings=resolved_settings,
            resolved_delivery=resolved_delivery,
            access_token=access_token,
        )
    return EmailConnectionStatus(
        host=_gmail_api_host(resolved_settings),
        port=443,
        transport=resolved_delivery.transport,
        auth_mode=resolved_delivery.auth_mode,
        sender=resolved_delivery.from_email,
        reply_to=resolved_delivery.reply_to,
        warnings=resolved_delivery.warnings,
    )


def get_email_delivery_summary(settings: Settings | None = None) -> dict[str, object]:
    from . import get_settings, validate_email_delivery_settings
    from .config import _gmail_api_host

    resolved_settings = settings or get_settings()
    resolved_delivery = validate_email_delivery_settings(resolved_settings)
    return {
        "transport": resolved_delivery.transport,
        "host": _gmail_api_host(resolved_settings),
        "port": 443,
        "auth_mode": resolved_delivery.auth_mode,
        "sender": resolved_delivery.from_email,
        "reply_to": resolved_delivery.reply_to,
        "google_account_type": resolved_delivery.google_account_type,
        "warnings": list(resolved_delivery.warnings),
    }


def send_test_email(
    *,
    recipient_email: str,
    subject: str | None = None,
    body: str | None = None,
) -> None:
    resolved_subject = subject or "VALID8 Gmail API connectivity test"
    resolved_body = body or (
        "This is a production-style Gmail API smoke test from VALID8.\n\n"
        "If you received this email, the backend refreshed a Google OAuth token "
        "and completed a real Gmail API delivery attempt."
    )
    send_transactional_email(
        recipient_email=recipient_email,
        subject=resolved_subject,
        text_body=resolved_body,
        html_body=(
            "<p>This is a production-style Gmail API smoke test from <strong>VALID8</strong>.</p>"
            "<p>If you received this email, the backend refreshed a Google OAuth token "
            "and completed a real Gmail API delivery attempt.</p>"
        ),
    )

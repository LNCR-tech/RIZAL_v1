"""Transport helpers for the Mailjet-backed email service package."""

from __future__ import annotations

from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from urllib.parse import urlparse

from app.core.config import Settings

from .config import (
    TEMPORARY_MAILJET_STATUS_CODES,
    EmailConnectionStatus,
    EmailDeliveryError,
)


def _mailjet_timeout(settings: Settings) -> float:
    return float(settings.email_timeout_seconds)


def _mailjet_rest_sender_url(settings: Settings) -> str:
    parsed = urlparse(settings.mailjet_api_base_url)
    scheme = parsed.scheme or "https"
    host = parsed.netloc or "api.mailjet.com"
    return f"{scheme}://{host}/v3/REST/sender"


def _extract_mailjet_error_detail(response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return (response.text or response.reason_phrase or "").strip()

    if isinstance(payload, dict):
        messages = payload.get("Messages")
        if isinstance(messages, list):
            errors: list[str] = []
            for message in messages:
                if not isinstance(message, dict):
                    continue
                message_errors = message.get("Errors") or []
                for item in message_errors:
                    if not isinstance(item, dict):
                        continue
                    identifier = str(item.get("ErrorIdentifier") or "").strip()
                    message_text = str(item.get("ErrorMessage") or "").strip()
                    detail = ": ".join(part for part in [identifier, message_text] if part)
                    if detail:
                        errors.append(detail)
                if not errors:
                    status = str(message.get("Status") or "").strip()
                    if status:
                        errors.append(status)
            if errors:
                return "; ".join(errors)

        for key in ("ErrorMessage", "ErrorInfo", "message"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return (response.text or response.reason_phrase or "").strip()


def _mailjet_auth(settings: Settings) -> tuple[str, str]:
    return (settings.mailjet_api_key, settings.mailjet_api_secret)


def _extract_message_part(msg: EmailMessage, subtype: str) -> str:
    if msg.is_multipart():
        part = msg.get_body(preferencelist=(subtype,))
        if part is None:
            return ""
        return str(part.get_content()).strip()
    if subtype == "plain":
        return str(msg.get_content()).strip()
    return ""


def _build_mailjet_payload(
    *,
    resolved_delivery,
    msg: EmailMessage,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "From": {
            "Email": resolved_delivery.sender_email,
            "Name": resolved_delivery.sender_name,
        },
        "To": [{"Email": msg["To"]}],
        "Subject": msg["Subject"],
        "TextPart": _extract_message_part(msg, "plain"),
    }

    html_body = _extract_message_part(msg, "html")
    if html_body:
        payload["HTMLPart"] = html_body
    if resolved_delivery.reply_to:
        payload["ReplyTo"] = {
            "Email": resolved_delivery.reply_to,
            "Name": resolved_delivery.sender_name,
        }

    return {"Messages": [payload]}


def _send_via_mailjet_api(
    *,
    settings: Settings,
    resolved_delivery,
    msg: EmailMessage,
) -> None:
    from . import httpx

    payload = _build_mailjet_payload(
        resolved_delivery=resolved_delivery,
        msg=msg,
    )

    try:
        response = httpx.post(
            settings.mailjet_api_base_url,
            auth=_mailjet_auth(settings),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=_mailjet_timeout(settings),
        )
    except httpx.TimeoutException as exc:
        raise EmailDeliveryError(
            "Timed out while calling the Mailjet API. Check outbound HTTPS access from the deployment host."
        ) from exc
    except httpx.HTTPError as exc:
        raise EmailDeliveryError(
            "Could not reach the Mailjet API send endpoint. Check outbound HTTPS access from the deployment host."
        ) from exc

    if response.status_code < 300:
        detail = _extract_mailjet_error_detail(response)
        if detail.lower() in {"success", "sent"} or not detail:
            return
        try:
            payload = response.json()
        except ValueError:
            return
        messages = payload.get("Messages") if isinstance(payload, dict) else None
        if isinstance(messages, list) and all(
            isinstance(message, dict) and str(message.get("Status") or "").strip().lower() == "success"
            for message in messages
        ):
            return

    detail = _extract_mailjet_error_detail(response)
    detail_lower = detail.lower()

    if response.status_code in {401, 403}:
        raise EmailDeliveryError(
            "Mailjet rejected the configured API credentials. Check MAILJET_API_KEY and MAILJET_API_SECRET."
        )
    if response.status_code == 400:
        raise EmailDeliveryError(
            f"Mailjet rejected the outbound email request: {detail or response.reason_phrase}"
        )
    if response.status_code in TEMPORARY_MAILJET_STATUS_CODES:
        raise EmailDeliveryError(
            f"Temporary Mailjet API failure ({response.status_code}). Retry later: {detail}"
        )
    if "sender" in detail_lower or "from" in detail_lower:
        raise EmailDeliveryError(
            f"Mailjet rejected the configured sender identity: {detail}"
        )
    raise EmailDeliveryError(
        f"Mailjet send failed with status {response.status_code}: {detail or response.reason_phrase}"
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
    msg["Message-ID"] = make_msgid(domain=resolved_delivery.sender_email.split("@", 1)[-1])
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

    if resolved_delivery.transport == "mailjet_api":
        _send_via_mailjet_api(
            settings=settings,
            resolved_delivery=resolved_delivery,
            msg=msg,
        )
        return
    raise EmailDeliveryError(
        f"Unsupported email transport configured: {resolved_delivery.transport}"
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
) -> EmailConnectionStatus:
    from . import (
        get_settings,
        logger,
        validate_email_delivery_settings,
    )
    from .config import _mailjet_api_host

    resolved_settings = settings or get_settings()
    resolved_delivery = validate_email_delivery_settings(resolved_settings)

    for warning in resolved_delivery.warnings:
        logger.warning(warning)

    if resolved_delivery.transport != "mailjet_api":
        raise EmailDeliveryError(
            f"Unsupported email transport configured: {resolved_delivery.transport}"
        )

    from . import httpx

    try:
        response = httpx.get(
            _mailjet_rest_sender_url(resolved_settings),
            auth=_mailjet_auth(resolved_settings),
            headers={"Accept": "application/json"},
            timeout=_mailjet_timeout(resolved_settings),
        )
    except httpx.TimeoutException as exc:
        raise EmailDeliveryError(
            "Timed out while calling the Mailjet API. Check outbound HTTPS access from the deployment host."
        ) from exc
    except httpx.HTTPError as exc:
        raise EmailDeliveryError(
            "Could not reach the Mailjet API verification endpoint. Check outbound HTTPS access from the deployment host."
        ) from exc

    if response.status_code >= 300:
        detail = _extract_mailjet_error_detail(response)
        if response.status_code in {401, 403}:
            raise EmailDeliveryError(
                "Mailjet rejected the configured API credentials. Check MAILJET_API_KEY and MAILJET_API_SECRET."
            )
        if response.status_code in TEMPORARY_MAILJET_STATUS_CODES:
            raise EmailDeliveryError(
                f"Temporary Mailjet API failure ({response.status_code}). Retry later: {detail}"
            )
        raise EmailDeliveryError(
            f"Mailjet connection verification failed with status {response.status_code}: {detail or response.reason_phrase}"
        )

    return EmailConnectionStatus(
        host=_mailjet_api_host(resolved_settings),
        port=443,
        transport=resolved_delivery.transport,
        auth_mode=resolved_delivery.auth_mode,
        sender=resolved_delivery.sender_email,
        reply_to=resolved_delivery.reply_to,
        warnings=resolved_delivery.warnings,
    )


def get_email_delivery_summary(settings: Settings | None = None) -> dict[str, object]:
    from . import get_settings, validate_email_delivery_settings
    from .config import _mailjet_api_host

    resolved_settings = settings or get_settings()
    resolved_delivery = validate_email_delivery_settings(resolved_settings)

    if resolved_delivery.transport != "mailjet_api":
        raise EmailDeliveryError(
            f"Unsupported email transport configured: {resolved_delivery.transport}"
        )

    return {
        "transport": resolved_delivery.transport,
        "host": _mailjet_api_host(resolved_settings),
        "port": 443,
        "auth_mode": resolved_delivery.auth_mode,
        "sender": resolved_delivery.sender_email,
        "reply_to": resolved_delivery.reply_to,
        "warnings": list(resolved_delivery.warnings),
    }


def send_test_email(
    *,
    recipient_email: str,
    subject: str | None = None,
    body: str | None = None,
) -> None:
    resolved_subject = subject or "Aura email transport connectivity test"
    resolved_body = body or (
        "This is a production-style email transport smoke test from Aura.\n\n"
        "If you received this email, the backend completed a real outbound email "
        "delivery attempt using the configured transport."
    )
    send_transactional_email(
        recipient_email=recipient_email,
        subject=resolved_subject,
        text_body=resolved_body,
        html_body=(
            "<p>This is a production-style email transport smoke test from <strong>Aura</strong>.</p>"
            "<p>If you received this email, the backend completed a real outbound email "
            "delivery attempt using the configured transport.</p>"
        ),
    )

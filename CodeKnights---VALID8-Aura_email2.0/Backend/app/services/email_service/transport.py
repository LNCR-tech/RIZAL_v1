# ======================================================
# GMAIL API HEADERS
# ======================================================

def build_gmail_api_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

DEFAULT_SENDER = "Aura System <noreply-aura@gmail.com>"


# ======================================================
# GMAIL HEADERS
# ======================================================

def build_gmail_api_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


# ======================================================
# TOKEN REQUEST
# ======================================================

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
            timeout=settings.email_timeout_seconds,
        )

        response.raise_for_status()

    except Exception as e:
        raise EmailDeliveryError(
            f"Failed to obtain Gmail OAuth token: {str(e)}"
        )

    access_token = response.json().get("access_token")

    if not access_token:
        raise EmailDeliveryError("No access token received")

    return access_token


# ======================================================
# BUILD MESSAGE
# ======================================================

def _build_message(
    *,
    resolved_delivery,
    recipient_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    reply_to: str | None = None,
) -> EmailMessage:

    if not subject.strip():
        raise EmailDeliveryError("Email subject cannot be empty")

    if not text_body.strip():
        raise EmailDeliveryError("Email body cannot be empty")

    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = DEFAULT_SENDER
    msg["To"] = recipient_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="aura-system.local")

    if reply_to:
        msg["Reply-To"] = reply_to

    msg.set_content(text_body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    return msg


# ======================================================
# ENCODE
# ======================================================

def _encode_message(msg: EmailMessage) -> str:
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


# ======================================================
# SEND EMAIL
# ======================================================

def _send_via_gmail_api(
    *,
    settings: Settings,
    resolved_delivery,
    msg: EmailMessage,
) -> None:

    from . import httpx

    access_token = _request_google_oauth_access_token(settings)

    send_url = (
        settings.google_gmail_api_base_url.rstrip("/")
        + "/users/me/messages/send"
    )

    payload = {
        "raw": _encode_message(msg)
    }

    try:

        response = httpx.post(
            send_url,
            headers=build_gmail_api_headers(access_token),
            json=payload,
            timeout=settings.email_timeout_seconds,
        )

    except Exception as e:
        raise EmailDeliveryError(
            f"Gmail API connection error: {str(e)}"
        )

    if response.status_code not in (200, 202):

        raise EmailDeliveryError(
            f"Gmail API send failed: {response.text}"
        )


# ======================================================
# MAIN SEND FUNCTION
# ======================================================

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
        validate_email_delivery_settings,
    )

    settings = get_settings()

    resolved_delivery = validate_email_delivery_settings(settings)

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


# ======================================================
# TEST EMAIL
# ======================================================

def send_test_email(
    *,
    recipient_email: str,
) -> None:

    send_transactional_email(
        recipient_email=recipient_email,
        subject="Aura System Test Email",
        text_body="""
Hello,

This is a test email from Aura System.

If you received this email,
the mailing system is working correctly.

Sender:
noreply-aura@gmail.com

Best Regards,
Aura System
        """,
        html_body="""
<h2>Aura System Test Email</h2>

<p>Hello,</p>

<p>This is a test email from Aura System.</p>

<p>If you received this email, the mailing system is working correctly.</p>

<p><b>Sender:</b> noreply-aura@gmail.com</p>

<p>Best Regards<br>
Aura System</p>
        """,
    )
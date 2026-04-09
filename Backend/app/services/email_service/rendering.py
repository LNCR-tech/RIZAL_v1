"""Template rendering helpers for the email service package."""

from __future__ import annotations

import html


# ======================================================
# SYSTEM CONFIG
# ======================================================

SYSTEM_EMAIL = "noreply-aura@gmail.com"
SYSTEM_NAME = "Aura System"


# ======================================================
# EMAIL FOOTERS
# ======================================================

EMAIL_FOOTER_TEXT = f"""
--------------------------------------------------

This is an automated email from {SYSTEM_NAME}.
Please do not reply.

Sender:
{SYSTEM_NAME}
{SYSTEM_EMAIL}

--------------------------------------------------
"""


EMAIL_FOOTER_HTML = f"""
<hr>

<p>
This is an automated email from <b>{SYSTEM_NAME}</b>.<br>
Please do not reply.
</p>

<p>
<b>{SYSTEM_NAME}</b><br>
{SYSTEM_EMAIL}
</p>
"""


# ======================================================
# SEND HELPER
# ======================================================

def _send_email(
    *,
    recipient_email: str,
    subject: str,
    text_body: str | None = None,
    body: str | None = None,
    html_body: str | None = None,
):

    from .transport import send_transactional_email

    send_transactional_email(
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body if text_body is not None else (body or ""),
        html_body=html_body,
    )


# ======================================================
# WELCOME EMAIL
# ======================================================

def build_welcome_email_content(
    *,
    recipient_email: str,
    temporary_password: str,
    first_name: str,
    system_name: str,
    login_url: str,
    password_label: str,
    credential_subject: str,
    password_notice: str,
) -> tuple[str, str, str]:

    subject = f"Welcome to {system_name}"

    text_body = f"""
Hello {first_name},

Welcome to {system_name}!

Your account has been created.

Email: {recipient_email}
{password_label}: {temporary_password}

Login URL: {login_url}

{password_notice}

{EMAIL_FOOTER_TEXT}
"""

    html_body = f"""
<h2>Welcome to {html.escape(system_name)}</h2>

<p>Hello {html.escape(first_name)},</p>

<p>Your account has been created.</p>

<p><b>{html.escape(credential_subject)}</b></p>

<p>
Email: {html.escape(recipient_email)}<br>
{html.escape(password_label)}: {html.escape(temporary_password)}
</p>

<p>
<a href="{html.escape(login_url)}">Login</a>
</p>

<p>{html.escape(password_notice).replace(chr(10), '<br>')}</p>

{EMAIL_FOOTER_HTML}
"""

    return subject, text_body, html_body


# ======================================================
# IMPORT ONBOARDING
# ======================================================

def build_import_onboarding_email_content(
    *,
    recipient_email: str,
    temporary_password: str,
    first_name: str,
    system_name: str,
    login_url: str,
) -> tuple[str, str, str]:

    subject = f"{system_name} Account Ready"

    text_body = f"""
Hello {first_name},

Your account has been created.
You can sign in using the login page below.
If you do not know your password, use the Forgot Password option on the login page.

Login URL: {login_url}

{EMAIL_FOOTER_TEXT}
"""

    html_body = f"""
<h3>Account Ready</h3>

<p>Hello {html.escape(first_name)}</p>

<p>Your account has been created and is ready to use.</p>

<p>
  <a href="{html.escape(login_url)}">Login</a>
</p>

<p>If you do not know your password, use the Forgot Password option on the login page.</p>

{EMAIL_FOOTER_HTML}
"""

    return subject, text_body, html_body


# ======================================================
# PASSWORD RESET
# ======================================================

def build_password_reset_email_content(
    *,
    recipient_email: str,
    temporary_password: str,
    first_name: str,
    system_name: str,
    login_url: str,
) -> tuple[str, str, str]:

    subject = f"{system_name} Password Reset"

    text_body = f"""
Hello {first_name},

Your password has been reset.

Temporary Password:
{temporary_password}

Login URL: {login_url}

You are required to change this temporary password immediately after login.

{EMAIL_FOOTER_TEXT}
"""

    html_body = f"""
<h3>Password Reset</h3>

<p>Hello {html.escape(first_name)}</p>

<p>
Temporary Password:
<b>{html.escape(temporary_password)}</b>
</p>

<p>
  <a href="{html.escape(login_url)}">Login</a>
</p>

<p><b>Temporary Login Credentials</b></p>

{EMAIL_FOOTER_HTML}
"""

    return subject, text_body, html_body


# ======================================================
# MFA EMAIL
# ======================================================

def build_mfa_code_email_content(
    *,
    code: str,
    first_name: str,
    system_name: str,
) -> tuple[str, str, str]:

    subject = f"{system_name} Verification Code"

    text_body = f"""
Hello {first_name},

Your verification code:

{code}

Expires in 10 minutes.

{EMAIL_FOOTER_TEXT}
"""

    html_body = f"""
<h3>Verification Code</h3>

<p>Hello {html.escape(first_name)}</p>

<h2>{html.escape(code)}</h2>

<p>Expires in 10 minutes</p>

{EMAIL_FOOTER_HTML}
"""

    return subject, text_body, html_body

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config import get_settings


class EmailDeliveryError(Exception):
    pass


def validate_email_delivery_settings() -> None:
    _validate_smtp_settings()


def _validate_smtp_settings() -> None:
    settings = get_settings()
    smtp_host = settings.smtp_host.strip().lower()
    smtp_from_email = settings.smtp_from_email.strip().lower()

    if not settings.smtp_host:
        raise EmailDeliveryError("SMTP_HOST is not configured")

    if smtp_host == "smtp.gmail.com":
        if not settings.smtp_username or not settings.smtp_password:
            raise EmailDeliveryError(
                "Gmail SMTP requires SMTP_USERNAME and SMTP_PASSWORD. "
                "Use a Gmail App Password or switch the Docker stack to a local SMTP server."
            )
        if smtp_from_email == "noreply@valid8.local":
            raise EmailDeliveryError(
                "SMTP_FROM_EMAIL is still using the placeholder noreply@valid8.local. "
                "Set it to the authenticated Gmail sender address."
            )


def _send_email(subject: str, recipient_email: str, body: str) -> None:
    settings = get_settings()
    validate_email_delivery_settings()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = recipient_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(msg)
    except Exception as exc:  # pragma: no cover - external dependency
        raise EmailDeliveryError(str(exc)) from exc


def send_plain_email(
    *,
    recipient_email: str,
    subject: str,
    body: str,
) -> None:
    _send_email(subject=subject, recipient_email=recipient_email, body=body)


def send_welcome_email(
    recipient_email: str,
    temporary_password: str,
    first_name: Optional[str] = None,
    system_name: Optional[str] = None,
    login_url: Optional[str] = None,
) -> None:
    settings = get_settings()

    resolved_first_name = (first_name or "").strip() or "User"
    resolved_system_name = (system_name or "").strip() or "Valid8 Attendance Recognition System"
    resolved_login_url = (login_url or "").strip() or settings.login_url

    _send_email(
        subject=f"Welcome to {resolved_system_name} – Temporary Login Credentials",
        recipient_email=recipient_email,
        body=(
            f"Dear {resolved_first_name},\n\n"
            f"Welcome to {resolved_system_name}!\n\n"
            "Your account has been successfully created.\n\n"
            "Login Credentials:\n"
            "-----------------------------------\n"
            f"Email: {recipient_email}\n"
            f"Temporary Password: {temporary_password}\n"
            f"Login URL: {resolved_login_url}\n"
            "-----------------------------------\n\n"
            "IMPORTANT:\n"
            "For security reasons, this is a temporary password.\n"
            "You are required to change your password immediately after your first login.\n\n"
            "Do not share your login credentials with anyone.\n\n"
            "If you experience issues, contact your School IT Administrator.\n\n"
            "Best regards,\n"
            f"{resolved_system_name} Team\n"
        ),
    )


def send_password_reset_email(
    recipient_email: str,
    temporary_password: str,
    first_name: Optional[str] = None,
    system_name: Optional[str] = None,
    login_url: Optional[str] = None,
) -> None:
    settings = get_settings()

    resolved_first_name = (first_name or "").strip() or "User"
    resolved_system_name = (system_name or "").strip() or "Valid8 Attendance Recognition System"
    resolved_login_url = (login_url or "").strip() or settings.login_url

    _send_email(
        subject=f"{resolved_system_name} – Password Reset Approved",
        recipient_email=recipient_email,
        body=(
            f"Dear {resolved_first_name},\n\n"
            "Your password reset request has been approved.\n\n"
            "Temporary Login Credentials:\n"
            "-----------------------------------\n"
            f"Email: {recipient_email}\n"
            f"Temporary Password: {temporary_password}\n"
            f"Login URL: {resolved_login_url}\n"
            "-----------------------------------\n\n"
            "IMPORTANT:\n"
            "You are required to change this temporary password immediately after login.\n\n"
            "Best regards,\n"
            f"{resolved_system_name} Team\n"
        ),
    )


def send_mfa_code_email(
    *,
    recipient_email: str,
    code: str,
    first_name: Optional[str] = None,
    system_name: Optional[str] = None,
) -> None:
    resolved_first_name = (first_name or "").strip() or "User"
    resolved_system_name = (system_name or "").strip() or "Valid8 Attendance Recognition System"
    _send_email(
        subject=f"{resolved_system_name} – MFA Verification Code",
        recipient_email=recipient_email,
        body=(
            f"Dear {resolved_first_name},\n\n"
            "Use the code below to complete your login:\n\n"
            f"MFA Code: {code}\n\n"
            "This code expires in 10 minutes.\n"
            "If you did not attempt to log in, please reset your password immediately.\n\n"
            f"{resolved_system_name} Team\n"
        ),
    )

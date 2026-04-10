"""Use: Contains the main backend rules for password change policy checks.
Where to use: Use this from routers, workers, or other services when password change policy checks logic is needed.
Role: Service layer. It keeps business logic out of the route files.
"""

from __future__ import annotations


NEW_ACCOUNT_MUST_CHANGE_PASSWORD = False
RESET_ACCOUNT_MUST_CHANGE_PASSWORD = True
NEW_ACCOUNT_SHOULD_PROMPT_PASSWORD_CHANGE = True
RESET_ACCOUNT_SHOULD_PROMPT_PASSWORD_CHANGE = False


def must_change_password_for_new_account() -> bool:
    return NEW_ACCOUNT_MUST_CHANGE_PASSWORD


def must_change_password_for_temporary_reset() -> bool:
    return RESET_ACCOUNT_MUST_CHANGE_PASSWORD


def should_prompt_password_change_for_new_account() -> bool:
    return NEW_ACCOUNT_SHOULD_PROMPT_PASSWORD_CHANGE


def should_prompt_password_change_for_temporary_reset() -> bool:
    return RESET_ACCOUNT_SHOULD_PROMPT_PASSWORD_CHANGE


def get_welcome_email_password_notice(*, password_is_temporary: bool = True) -> str:
    if password_is_temporary and must_change_password_for_new_account():
        return (
            "IMPORTANT:\n"
            "For security reasons, this is a temporary password.\n"
            "You are required to change your password immediately after your first login.\n\n"
        )

    if password_is_temporary:
        return (
            "IMPORTANT:\n"
            "For security reasons, this is a temporary password.\n"
            "You can keep using it after login, but changing it from your account settings is recommended.\n\n"
        )

    return (
        "IMPORTANT:\n"
        "Keep this password private.\n"
        "You can change it anytime from your account settings if you want a new one.\n\n"
    )

"""Use: Contains the main backend rules for per-user app and security settings.
Where to use: Use this from routers and auth/session services when loading or updating user-scoped preferences.
Role: Service layer. It keeps persistence defaults and validation out of route files.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import has_any_role
from app.models.platform_features import UserAppPreference, UserSecuritySetting
from app.models.user import User

APP_FONT_SIZE_MIN = 80
APP_FONT_SIZE_MAX = 130
APP_FONT_SIZE_STEP = 5
APP_FONT_SIZE_DEFAULT = 100
APP_TRUSTED_DEVICE_DAYS_DEFAULT = 14
APP_TRUSTED_DEVICE_DAYS_MIN = 1
APP_TRUSTED_DEVICE_DAYS_MAX = 90


def normalize_font_size_percent(value: int | float | None) -> int:
    numeric_value = int(value) if value is not None else APP_FONT_SIZE_DEFAULT
    stepped_value = round(numeric_value / APP_FONT_SIZE_STEP) * APP_FONT_SIZE_STEP
    return max(APP_FONT_SIZE_MIN, min(APP_FONT_SIZE_MAX, stepped_value))


def normalize_trusted_device_days(value: int | None) -> int:
    numeric_value = int(value) if value is not None else APP_TRUSTED_DEVICE_DAYS_DEFAULT
    return max(APP_TRUSTED_DEVICE_DAYS_MIN, min(APP_TRUSTED_DEVICE_DAYS_MAX, numeric_value))


def get_or_create_user_app_preference(db: Session, *, user_id: int) -> UserAppPreference:
    pref = (
        db.query(UserAppPreference)
        .filter(UserAppPreference.user_id == user_id)
        .first()
    )
    if pref:
        pref.font_size_percent = normalize_font_size_percent(pref.font_size_percent)
        return pref

    pref = UserAppPreference(
        user_id=user_id,
        dark_mode_enabled=False,
        font_size_percent=APP_FONT_SIZE_DEFAULT,
    )
    db.add(pref)
    db.flush()
    return pref


def _default_mfa_enabled_for_user(user: User) -> bool:
    return has_any_role(user, ["admin", "campus_admin"])


def get_or_create_user_security_setting(db: Session, *, user: User) -> UserSecuritySetting:
    setting = (
        db.query(UserSecuritySetting)
        .filter(UserSecuritySetting.user_id == user.id)
        .first()
    )
    if setting:
        setting.trusted_device_days = normalize_trusted_device_days(setting.trusted_device_days)
        return setting

    setting = UserSecuritySetting(
        user_id=user.id,
        mfa_enabled=_default_mfa_enabled_for_user(user),
        trusted_device_days=APP_TRUSTED_DEVICE_DAYS_DEFAULT,
    )
    db.add(setting)
    db.flush()
    return setting

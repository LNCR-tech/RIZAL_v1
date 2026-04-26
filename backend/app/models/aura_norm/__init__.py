"""Aura normalized schema models (aura_norm.*).

This module intentionally lives side-by-side with the current production models in `app.models.*`.

- It is aligned to the proposed schema in `db_normalized/new_db_schema.sql` (repo root).
- It is NOT wired into the running app by default, so existing endpoints keep working.
"""

from app.models.aura_norm.base import AURA_NORM_SCHEMA, AuraNormBase
from app.models.aura_norm.models import (  # noqa: F401
    AcademicPeriod,
    AttendanceMethod,
    AttendanceRecord,
    AttendanceStatus,
    Department,
    Event,
    EventType,
    GovernanceMember,
    GovernancePermission,
    GovernanceUnit,
    NotificationChannel,
    NotificationTopic,
    Program,
    Role,
    SanctionItemTemplate,
    SanctionRecord,
    School,
    SubscriptionPlan,
    User,
    UserNotificationPreference,
    UserRole,
)

__all__ = [
    "AURA_NORM_SCHEMA",
    "AuraNormBase",
    "AcademicPeriod",
    "AttendanceMethod",
    "AttendanceRecord",
    "AttendanceStatus",
    "Department",
    "Event",
    "EventType",
    "GovernanceMember",
    "GovernancePermission",
    "GovernanceUnit",
    "NotificationChannel",
    "NotificationTopic",
    "Program",
    "Role",
    "SanctionItemTemplate",
    "SanctionRecord",
    "School",
    "SubscriptionPlan",
    "User",
    "UserNotificationPreference",
    "UserRole",
]


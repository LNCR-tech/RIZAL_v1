"""Use: Marks `models` as a Python package and groups related backend files.
Where to use: Used automatically when Python imports modules from `models`.
Role: Package layer. It helps the backend treat this folder as one importable package.
"""

# Import all models here so they can be imported elsewhere with a single import 
# The order of imports is important here - import base first
from app.models.base import Base
from app.models.department import Department
from app.models.face_recognition import UserFaceRecognitionProfile
from app.models.program import Program
from app.models.event import Event
from app.models.event_type import EventType
from app.models.school import School, SchoolSetting, SchoolAuditLog
from app.models.import_job import BulkImportJob, BulkImportError, EmailDeliveryLog
from app.models.password_reset_request import PasswordResetRequest
from app.models.platform_features import (
    UserAppPreference,
    UserNotificationPreference,
    NotificationLog,
    UserSecuritySetting,
    UserFaceProfile,
    MfaChallenge,
    UserSession,
    LoginHistory,
    SchoolSubscriptionSetting,
    SchoolSubscriptionReminder,
    DataGovernanceSetting,
    UserPrivacyConsent,
    DataRequest,
    DataRetentionRunLog,
)
from app.models.governance_hierarchy import (
    GovernanceAnnouncement,
    GovernanceMember,
    GovernanceMemberPermission,
    GovernancePermission,
    GovernanceStudentNote,
    GovernanceUnit,
    GovernanceUnitPermission,
)
from app.models.sanctions import (
    ClearanceDeadline,
    EventSanctionConfig,
    SanctionComplianceHistory,
    SanctionDelegation,
    SanctionItem,
    SanctionRecord,
)

from .role import Role
from .user import User, UserRole, StudentProfile, FacultyProfile
from .attendance import Attendance  # If you have this model

__all__ = [
    "Base",
    "Role",
    "User",
    "UserRole",
    "StudentProfile",
    "FacultyProfile",
    "Attendance",
    "School",
    "SchoolSetting",
    "SchoolAuditLog",
    "BulkImportJob",
    "BulkImportError",
    "EmailDeliveryLog",
    "PasswordResetRequest",
    "UserAppPreference",
    "UserNotificationPreference",
    "NotificationLog",
    "UserSecuritySetting",
    "UserFaceProfile",
    "UserFaceRecognitionProfile",
    "MfaChallenge",
    "UserSession",
    "LoginHistory",
    "SchoolSubscriptionSetting",
    "SchoolSubscriptionReminder",
    "DataGovernanceSetting",
    "UserPrivacyConsent",
    "DataRequest",
    "DataRetentionRunLog",
    "GovernanceUnit",
    "GovernanceMember",
    "GovernanceMemberPermission",
    "GovernancePermission",
    "GovernanceUnitPermission",
    "GovernanceAnnouncement",
    "GovernanceStudentNote",
    "EventSanctionConfig",
    "EventType",
    "SanctionRecord",
    "SanctionItem",
    "SanctionDelegation",
    "SanctionComplianceHistory",
    "ClearanceDeadline",
]

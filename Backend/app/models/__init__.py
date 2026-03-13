# Import all models here so they can be imported elsewhere with a single import 
# The order of imports is important here - import base first
from app.models.base import Base
from app.models.department import Department
from app.models.face_recognition import UserFaceRecognitionProfile
from app.models.program import Program
from app.models.event import Event
from app.models.school import School, SchoolSetting, SchoolAuditLog
from app.models.import_job import BulkImportJob, BulkImportError, EmailDeliveryLog
from app.models.password_reset_request import PasswordResetRequest
from app.models.platform_features import (
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

from .role import Role
from .user import User, UserRole, StudentProfile, SSGProfile
from .attendance import Attendance  # If you have this model

__all__ = [
    "Base",
    "Role",
    "User",
    "UserRole",
    "StudentProfile",
    "SSGProfile",
    "Attendance",
    "School",
    "SchoolSetting",
    "SchoolAuditLog",
    "BulkImportJob",
    "BulkImportError",
    "EmailDeliveryLog",
    "PasswordResetRequest",
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
]

"""Use: Defines database models for platform feature flags and subscriptions.
Where to use: Use this when the backend needs to store or load platform feature flags and subscriptions data.
Role: Model layer. It maps Python objects to database tables and relationships.
"""

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    email_enabled = Column(Boolean, nullable=False, default=True)
    sms_enabled = Column(Boolean, nullable=False, default=False)
    sms_number = Column(String(40), nullable=True)
    notify_missed_events = Column(Boolean, nullable=False, default=True)
    notify_low_attendance = Column(Boolean, nullable=False, default=True)
    notify_account_security = Column(Boolean, nullable=False, default=True)
    notify_subscription = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class UserAppPreference(Base):
    __tablename__ = "user_app_preferences"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dark_mode_enabled = Column(Boolean, nullable=False, default=False)
    font_size_percent = Column(Integer, nullable=False, default=100)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), nullable=False, default="email")
    status = Column(String(20), nullable=False, default="queued", index=True)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    school = relationship("School")
    user = relationship("User")


class UserSecuritySetting(Base):
    __tablename__ = "user_security_settings"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    trusted_device_days = Column(Integer, nullable=False, default=14)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class UserFaceProfile(Base):
    __tablename__ = "user_face_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    face_encoding = Column(LargeBinary, nullable=False)
    provider = Column(String(50), nullable=False, default="arcface")
    reference_image_sha256 = Column(String(64), nullable=True)
    last_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="face_profile")


class MfaChallenge(Base):
    __tablename__ = "mfa_challenges"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(255), nullable=False)
    channel = Column(String(20), nullable=False, default="email")
    attempts = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime, nullable=False, index=True)
    consumed_at = Column(DateTime, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_jti = Column(String(64), nullable=False, unique=True, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)

    user = relationship("User")


class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True)
    email_attempted = Column(String(255), nullable=False, index=True)
    success = Column(Boolean, nullable=False, default=False, index=True)
    auth_method = Column(String(30), nullable=False, default="password")
    failure_reason = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User")
    school = relationship("School")


class SchoolSubscriptionSetting(Base):
    __tablename__ = "school_subscription_settings"

    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True)
    plan_name = Column(String(50), nullable=False, default="free")
    user_limit = Column(Integer, nullable=False, default=500)
    event_limit_monthly = Column(Integer, nullable=False, default=100)
    import_limit_monthly = Column(Integer, nullable=False, default=10)
    renewal_date = Column(Date, nullable=True)
    auto_renew = Column(Boolean, nullable=False, default=False)
    reminder_days_before = Column(Integer, nullable=False, default=14)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    school = relationship("School")
    updated_by_user = relationship("User")


class SchoolSubscriptionReminder(Base):
    __tablename__ = "school_subscription_reminders"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_type = Column(String(40), nullable=False, default="renewal_warning")
    status = Column(String(20), nullable=False, default="pending", index=True)
    due_at = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    school = relationship("School")


class DataGovernanceSetting(Base):
    __tablename__ = "data_governance_settings"

    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True)
    attendance_retention_days = Column(Integer, nullable=False, default=1095)
    audit_log_retention_days = Column(Integer, nullable=False, default=3650)
    import_file_retention_days = Column(Integer, nullable=False, default=180)
    auto_delete_enabled = Column(Boolean, nullable=False, default=False)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    school = relationship("School")
    updated_by_user = relationship("User")


class UserPrivacyConsent(Base):
    __tablename__ = "user_privacy_consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(50), nullable=False, index=True)
    consent_granted = Column(Boolean, nullable=False, default=True)
    consent_version = Column(String(20), nullable=False, default="v1")
    source = Column(String(50), nullable=False, default="web")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User")
    school = relationship("School")


class DataRequest(Base):
    __tablename__ = "data_requests"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    request_type = Column(String(20), nullable=False, index=True)  # export | delete
    scope = Column(String(50), nullable=False, default="user_data")
    status = Column(String(20), nullable=False, default="pending", index=True)
    reason = Column(Text, nullable=True)
    details_json = Column(JSON, nullable=True)
    output_path = Column(String(1024), nullable=True)
    handled_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    school = relationship("School")
    requested_by_user = relationship("User", foreign_keys=[requested_by_user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    handled_by_user = relationship("User", foreign_keys=[handled_by_user_id])


class DataRetentionRunLog(Base):
    __tablename__ = "data_retention_run_logs"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    dry_run = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default="completed")
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    school = relationship("School")

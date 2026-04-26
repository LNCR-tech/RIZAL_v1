from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, LargeBinary, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.timezones import utc_now
from app.models.base import Base


class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    email_enabled = Column(Boolean, nullable=False, default=True)
    sms_enabled = Column(Boolean, nullable=False, default=False)
    sms_number = Column(Text, nullable=True)
    notify_missed_events = Column(Boolean, nullable=False, default=True)
    notify_low_attendance = Column(Boolean, nullable=False, default=True)
    notify_account_security = Column(Boolean, nullable=False, default=True)
    notify_subscription = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User")


class UserAppPreference(Base):
    __tablename__ = "user_app_preferences"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dark_mode_enabled = Column(Boolean, nullable=False, default=False)
    font_size_percent = Column(Integer, nullable=False, default=100)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User")


class UserSecuritySetting(Base):
    __tablename__ = "user_security_settings"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    trusted_device_days = Column(Integer, nullable=False, default=14)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User")


class UserFaceProfile(Base):
    __tablename__ = "user_face_profiles"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    face_encoding = Column(LargeBinary, nullable=False)
    provider = Column(Text, nullable=False, default="arcface")
    embedding_dtype = Column(Text, nullable=True)
    embedding_dimension = Column(Integer, nullable=True)
    embedding_normalized = Column(Boolean, nullable=False, default=True)
    reference_image_sha256 = Column(Text, nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="face_profile")


class MfaChallenge(Base):
    __tablename__ = "mfa_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(Text, nullable=False)
    channel = Column(Text, nullable=False, default="email")
    attempts = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    user = relationship("User")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_jti = Column(Text, nullable=False, unique=True, index=True)
    ip_address = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    user = relationship("User")


class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True)
    email_attempted = Column(Text, nullable=False, index=True)
    success = Column(Boolean, nullable=False, default=False, index=True)
    auth_method = Column(Text, nullable=False, default="password")
    failure_reason = Column(Text, nullable=True)
    ip_address = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    user = relationship("User")
    school = relationship("School")


class SchoolSubscriptionReminder(Base):
    __tablename__ = "school_subscription_reminders"

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_type = Column(Text, nullable=False, default="renewal_warning")
    status = Column(Text, nullable=False, default="pending", index=True)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    school = relationship("School")


class DataGovernanceSetting(Base):
    __tablename__ = "data_governance_settings"

    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True)
    attendance_retention_days = Column(Integer, nullable=False, default=1095)
    audit_log_retention_days = Column(Integer, nullable=False, default=3650)
    import_file_retention_days = Column(Integer, nullable=False, default=180)
    auto_delete_enabled = Column(Boolean, nullable=False, default=False)
    updated_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    school = relationship("School")
    updated_by_user = relationship("User")


class UserPrivacyConsent(Base):
    __tablename__ = "user_privacy_consents"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type_code = Column(Text, ForeignKey("privacy_consent_types.code", ondelete="RESTRICT"), nullable=False, index=True)
    consent_granted = Column(Boolean, nullable=False, default=True)
    consent_version = Column(Text, nullable=False, default="v1")
    source = Column(Text, nullable=False, default="web")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    user = relationship("User")
    school = relationship("School")

    # Compatibility property
    @property
    def consent_type(self) -> str:
        return self.consent_type_code

    @consent_type.setter
    def consent_type(self, value: str) -> None:
        self.consent_type_code = value


class DataRequest(Base):
    __tablename__ = "data_requests"

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    request_type = Column(Text, nullable=False, index=True)
    scope = Column(Text, nullable=False, default="user_data")
    status = Column(Text, nullable=False, default="pending", index=True)
    reason = Column(Text, nullable=True)
    output_path = Column(Text, nullable=True)
    handled_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    school = relationship("School")
    requested_by_user = relationship("User", foreign_keys=[requested_by_user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    handled_by_user = relationship("User", foreign_keys=[handled_by_user_id])


class DataRetentionRunLog(Base):
    __tablename__ = "data_retention_run_logs"

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    dry_run = Column(Boolean, nullable=False, default=True)
    status = Column(Text, nullable=False, default="completed")
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    school = relationship("School")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(Text, nullable=False, index=True)
    channel = Column(Text, nullable=False, default="email")
    status = Column(Text, nullable=False, default="queued", index=True)
    subject = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    school = relationship("School")
    user = relationship("User")


# Compatibility aliases
SchoolSubscriptionSetting = None  # replaced by SchoolSubscription in school.py

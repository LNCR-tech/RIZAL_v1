from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.core.event_defaults import (
    DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES,
    DEFAULT_EVENT_LATE_THRESHOLD_MINUTES,
    DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES,
)
from app.core.timezones import utc_now
from app.models.base import Base


class School(Base):
    __tablename__ = "schools"

    id = Column(BigInteger, primary_key=True)
    school_code = Column(Text, unique=True, nullable=True, index=True)
    legal_name = Column(Text, nullable=False)
    display_name = Column(Text, nullable=False, index=True)
    address = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Compatibility properties for old code that used school_name / name
    @property
    def school_name(self) -> str:
        return self.display_name

    @school_name.setter
    def school_name(self, value: str) -> None:
        self.display_name = value

    @property
    def name(self) -> str:
        return self.legal_name

    @name.setter
    def name(self, value: str) -> None:
        self.legal_name = value

    @property
    def active_status(self) -> bool:
        return self.is_active

    users = relationship("User", back_populates="school")
    student_profiles = relationship("StudentProfile", back_populates="school")
    events = relationship("Event", back_populates="school")
    event_types = relationship("EventType", back_populates="school", cascade="all, delete-orphan")
    audit_logs = relationship("SchoolAuditLog", back_populates="school", cascade="all, delete-orphan")
    branding = relationship("SchoolBranding", back_populates="school", uselist=False, cascade="all, delete-orphan")
    event_policies = relationship("SchoolEventPolicy", back_populates="school", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("SchoolSubscription", back_populates="school", uselist=False, cascade="all, delete-orphan")

    # Compatibility alias — old code accessed school.settings
    @property
    def settings(self):
        return self.event_policies


class SchoolBranding(Base):
    __tablename__ = "school_branding"

    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True)
    logo_url = Column(Text, nullable=True)
    primary_color = Column(Text, nullable=False, default="#162F65")
    secondary_color = Column(Text, nullable=True)
    accent_color = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    updated_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school = relationship("School", back_populates="branding")


class SchoolEventPolicy(Base):
    __tablename__ = "school_event_policies"

    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True)
    default_early_check_in_minutes = Column(Integer, nullable=False, default=DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES)
    default_late_threshold_minutes = Column(Integer, nullable=False, default=DEFAULT_EVENT_LATE_THRESHOLD_MINUTES)
    default_sign_out_grace_minutes = Column(Integer, nullable=False, default=DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    updated_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school = relationship("School", back_populates="event_policies")

    # Compatibility properties for old code that used school_settings column names
    @property
    def event_default_early_check_in_minutes(self) -> int:
        return self.default_early_check_in_minutes

    @property
    def event_default_late_threshold_minutes(self) -> int:
        return self.default_late_threshold_minutes

    @property
    def event_default_sign_out_grace_minutes(self) -> int:
        return self.default_sign_out_grace_minutes


class SchoolSubscription(Base):
    __tablename__ = "school_subscriptions"

    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True)
    plan_id = Column(BigInteger, ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False)
    status = Column(Text, nullable=False, default="trial")
    starts_on = Column(Date, nullable=False)
    ends_on = Column(Date, nullable=True)
    renewal_date = Column(Date, nullable=True)
    auto_renew = Column(Boolean, nullable=False, default=False)
    reminder_days_before = Column(Integer, nullable=False, default=14)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    updated_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school = relationship("School", back_populates="subscription")


class SchoolAuditLog(Base):
    __tablename__ = "school_audit_logs"

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="success")
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    school = relationship("School", back_populates="audit_logs")


# Compatibility alias — old code imported SchoolSetting
SchoolSetting = SchoolEventPolicy

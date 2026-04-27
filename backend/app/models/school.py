from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, synonym
from sqlalchemy.ext.hybrid import hybrid_property

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

    school_name = synonym("display_name")
    name = synonym("legal_name")
    active_status = synonym("is_active")

    users = relationship("User", back_populates="school")
    student_profiles = relationship("StudentProfile", back_populates="school")
    events = relationship("Event", back_populates="school")
    event_types = relationship("EventType", back_populates="school", cascade="all, delete-orphan")
    audit_logs = relationship("SchoolAuditLog", back_populates="school", cascade="all, delete-orphan")
    branding = relationship("SchoolBranding", back_populates="school", uselist=False, cascade="all, delete-orphan")
    event_policies = relationship("SchoolEventPolicy", back_populates="school", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("SchoolSubscription", back_populates="school", uselist=False, cascade="all, delete-orphan")

    # Compatibility alias for old code that accessed school.settings
    settings = synonym("event_policies")

    @property
    def logo_url(self) -> str | None:
        return self.branding.logo_url if self.branding is not None else None

    @logo_url.setter
    def logo_url(self, value: str | None) -> None:
        if self.branding is None:
            self.branding = SchoolBranding()
        self.branding.logo_url = value

    @property
    def primary_color(self) -> str | None:
        return self.branding.primary_color if self.branding is not None else None

    @primary_color.setter
    def primary_color(self, value: str | None) -> None:
        if self.branding is None:
            self.branding = SchoolBranding()
        self.branding.primary_color = value

    @property
    def secondary_color(self) -> str | None:
        return self.branding.secondary_color if self.branding is not None else None

    @secondary_color.setter
    def secondary_color(self, value: str | None) -> None:
        if self.branding is None:
            self.branding = SchoolBranding()
        self.branding.secondary_color = value

    @property
    def subscription_status(self) -> str | None:
        if self.subscription is not None:
            return self.subscription.status
        return self.__dict__.get("_compat_subscription_status")

    @subscription_status.setter
    def subscription_status(self, value: str | None) -> None:
        self.__dict__["_compat_subscription_status"] = value

    @property
    def subscription_plan(self) -> str | None:
        if self.subscription is not None and self.subscription.plan is not None:
            return self.subscription.plan.code
        return self.__dict__.get("_compat_subscription_plan")

    @subscription_plan.setter
    def subscription_plan(self, value: str | None) -> None:
        self.__dict__["_compat_subscription_plan"] = value

    @property
    def subscription_start(self):
        if self.subscription is not None:
            return self.subscription.starts_on
        return self.__dict__.get("_compat_subscription_start")

    @subscription_start.setter
    def subscription_start(self, value) -> None:
        self.__dict__["_compat_subscription_start"] = value

    @property
    def subscription_end(self):
        if self.subscription is not None:
            return self.subscription.ends_on
        return self.__dict__.get("_compat_subscription_end")

    @subscription_end.setter
    def subscription_end(self, value) -> None:
        self.__dict__["_compat_subscription_end"] = value


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
    @hybrid_property
    def event_default_early_check_in_minutes(self) -> int:
        return self.default_early_check_in_minutes

    @hybrid_property
    def event_default_late_threshold_minutes(self) -> int:
        return self.default_late_threshold_minutes

    @hybrid_property
    def event_default_sign_out_grace_minutes(self) -> int:
        return self.default_sign_out_grace_minutes



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

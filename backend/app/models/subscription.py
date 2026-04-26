from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.core.timezones import utc_now
from app.models.base import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(BigInteger, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    display_name = Column(Text, nullable=False)
    user_limit = Column(Integer, nullable=False)
    event_limit_monthly = Column(Integer, nullable=False)
    import_limit_monthly = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


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
    plan = relationship("SubscriptionPlan")
    updated_by_user = relationship("User")


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

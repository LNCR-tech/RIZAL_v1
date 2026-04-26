from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.timezones import utc_now
from app.models.base import Base


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    code = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)
    supports_address = Column(Boolean, nullable=False, default=False)


class NotificationTopic(Base):
    __tablename__ = "notification_topics"

    code = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)


class UserNotificationChannelSetting(Base):
    __tablename__ = "user_notification_channel_settings"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    channel_code = Column(Text, ForeignKey("notification_channels.code", ondelete="RESTRICT"), primary_key=True)
    enabled = Column(Boolean, nullable=False)
    address_value = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User")
    channel = relationship("NotificationChannel")


class UserNotificationTopicSetting(Base):
    __tablename__ = "user_notification_topic_settings"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    topic_code = Column(Text, ForeignKey("notification_topics.code", ondelete="RESTRICT"), primary_key=True)
    enabled = Column(Boolean, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User")
    topic = relationship("NotificationTopic")


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
    attributes = relationship("NotificationLogAttribute", back_populates="log", cascade="all, delete-orphan")


class NotificationLogAttribute(Base):
    __tablename__ = "notification_log_attributes"

    notification_log_id = Column(BigInteger, ForeignKey("notification_logs.id", ondelete="CASCADE"), primary_key=True)
    attribute_key = Column(Text, primary_key=True)
    attribute_value = Column(Text, nullable=True)

    log = relationship("NotificationLog", back_populates="attributes")

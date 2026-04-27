from __future__ import annotations

from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, Text, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship, synonym

from app.core.event_defaults import (
    DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES,
    DEFAULT_EVENT_LATE_THRESHOLD_MINUTES,
    DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES,
)
from app.core.timezones import utc_now
from app.models.base import Base
from app.models.associations import event_departments, event_programs


class EventStatus(PyEnum):
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("created_by_user_id", "create_idempotency_key", name="events_created_by_user_id_create_idempotency_key_key"),
    )

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type_id = Column(BigInteger, ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    create_idempotency_key = Column(Text, nullable=True)
    name = Column(Text, nullable=False)
    location = Column(Text, nullable=True)
    geo_latitude = Column(Float, nullable=True)
    geo_longitude = Column(Float, nullable=True)
    geo_radius_m = Column(Float, nullable=True)
    geo_required = Column(Boolean, nullable=False, default=False)
    geo_max_accuracy_m = Column(Float, nullable=True)
    early_check_in_minutes = Column(Integer, nullable=False, default=DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES)
    late_threshold_minutes = Column(Integer, nullable=False, default=DEFAULT_EVENT_LATE_THRESHOLD_MINUTES)
    sign_out_grace_minutes = Column(Integer, nullable=False, default=DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES)
    sign_out_open_delay_minutes = Column(Integer, nullable=False, default=0)
    sign_out_override_until = Column(DateTime(timezone=True), nullable=True)
    present_until_override_at = Column(DateTime(timezone=True), nullable=True)
    late_until_override_at = Column(DateTime(timezone=True), nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        SQLEnum(
            EventStatus,
            native_enum=False,
            length=50,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=EventStatus.UPCOMING,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    school = relationship("School", back_populates="events")
    event_type = relationship("EventType", back_populates="events")
    created_by_user = relationship("User")
    departments = relationship("Department", secondary=event_departments, back_populates="events")
    programs = relationship("Program", secondary=event_programs, back_populates="events")
    attendance_records = relationship("AttendanceRecord", back_populates="event", cascade="all, delete-orphan")

    # Compatibility aliases for old field names.
    start_datetime = synonym("start_at")
    end_datetime = synonym("end_at")
    attendances = synonym("attendance_records")

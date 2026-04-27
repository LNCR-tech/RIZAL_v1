from __future__ import annotations

from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, synonym

from app.core.timezones import utc_now
from app.models.base import Base


class AttendanceStatus(PyEnum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    EXCUSED = "excused"


class AttendanceMethodLookup(Base):
    __tablename__ = "attendance_methods"
    code = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)


class AttendanceStatusLookup(Base):
    __tablename__ = "attendance_statuses"
    code = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "event_id", name="attendance_records_student_profile_id_event_id_key"),
    )

    id = Column(BigInteger, primary_key=True)
    student_profile_id = Column(BigInteger, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(BigInteger, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    time_in = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    time_out = Column(DateTime(timezone=True), nullable=True)
    method_code = Column(Text, ForeignKey("attendance_methods.code", ondelete="RESTRICT"), nullable=False)
    status_code = Column(Text, ForeignKey("attendance_statuses.code", ondelete="RESTRICT"), nullable=False, default="present")
    check_in_status = Column(Text, nullable=True)
    check_out_status = Column(Text, nullable=True)
    verified_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    geo_distance_m = Column(Float, nullable=True)
    geo_effective_distance_m = Column(Float, nullable=True)
    geo_latitude = Column(Float, nullable=True)
    geo_longitude = Column(Float, nullable=True)
    geo_accuracy_m = Column(Float, nullable=True)
    liveness_label = Column(Text, nullable=True)
    liveness_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    student = relationship("StudentProfile", back_populates="attendance_records")
    event = relationship("Event", back_populates="attendance_records")

    @hybrid_property
    def status(self) -> str:
        return self.status_code

    @status.setter
    def status(self, value) -> None:
        self.status_code = value.value if isinstance(value, AttendanceStatus) else value

    method = synonym("method_code")
    student_id = synonym("student_profile_id")
    verified_by = synonym("verified_by_user_id")


# Compatibility alias
Attendance = AttendanceRecord

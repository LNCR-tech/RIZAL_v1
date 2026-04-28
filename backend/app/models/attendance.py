"""Use: Defines database models for attendance records.
Where to use: Use this when the backend needs to store or load attendance records data.
Role: Model layer. It maps Python objects to database tables and relationships.
"""

# app/models/attendance.py
import logging
import traceback

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, event
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.models.base import Base
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

logger = logging.getLogger(__name__)

class AttendanceStatus(PyEnum):
    PRESENT = "present"  # Must match database exactly
    LATE = "late"
    ABSENT = "absent"
    EXCUSED = "excused"


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), index=True)
    # NULL when the student never signed in (excused, auto-absent).
    # No default: callers must explicitly pass a real timestamp via an authorized
    # sign-in endpoint, otherwise the row stays NULL.
    time_in = Column(DateTime(timezone=True), nullable=True)
    time_out = Column(DateTime(timezone=True), nullable=True)
    method = Column(String(50))  # "face_scan", "manual", etc.
    status = Column(
        PG_ENUM(
            'present', 'late', 'absent', 'excused',  # Explicit lowercase values
            name='attendancestatus',
            create_type=True  # Use existing type
        ),
        default='present',  # Lowercase default
        nullable=False
    )
    check_in_status = Column(String(16), nullable=True)
    check_out_status = Column(String(16), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))  # Who verified (SSG/admin)
    notes = Column(String(500))  # Reason for excused absence, etc.
    geo_distance_m = Column(Float, nullable=True)
    geo_effective_distance_m = Column(Float, nullable=True)
    geo_latitude = Column(Float, nullable=True)
    geo_longitude = Column(Float, nullable=True)
    geo_accuracy_m = Column(Float, nullable=True)
    liveness_label = Column(String(32), nullable=True)
    liveness_score = Column(Float, nullable=True)

    # Relationships
    student = relationship("StudentProfile", back_populates="attendances")
    event = relationship("Event")


@event.listens_for(Attendance.time_in, "set", propagate=True)
def _log_time_in_assignment(target, value, old_value, initiator):
    """Trace every assignment to Attendance.time_in.

    Helps detect unauthorized writes (e.g. a code path filling time_in for a
    student who never actually signed in). Only assignments that change the
    column are reported, and only at DEBUG so production logs are not flooded.
    """
    if value == old_value:
        return
    stack = "".join(traceback.format_stack(limit=8))
    logger.debug(
        "Attendance.time_in assignment: student_id=%s event_id=%s old=%s new=%s\n%s",
        getattr(target, "student_id", None),
        getattr(target, "event_id", None),
        old_value,
        value,
        stack,
    )

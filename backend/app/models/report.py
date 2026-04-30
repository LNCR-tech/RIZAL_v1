from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.timezones import utc_now
from app.models.base import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    report_type = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    parameters = Column(Text, nullable=True)   # JSON string
    status = Column(Text, nullable=False, default="pending")  # pending, completed, failed
    result_data = Column(Text, nullable=True)  # JSON string
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    school = relationship("School")
    created_by = relationship("User", foreign_keys=[created_by_user_id])

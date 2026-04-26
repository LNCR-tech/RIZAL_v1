from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.timezones import utc_now
from app.models.base import Base


class PasswordResetRequest(Base):
    __tablename__ = "password_reset_requests"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_email = Column(Text, nullable=False, index=True)
    status = Column(Text, nullable=False, default="pending", index=True)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    user = relationship("User", foreign_keys=[user_id])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by_user_id])
    school = relationship("School")

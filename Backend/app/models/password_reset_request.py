"""Use: Defines database models for password reset request records.
Where to use: Use this when the backend needs to store or load password reset request records data.
Role: Model layer. It maps Python objects to database tables and relationships.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class PasswordResetRequest(Base):
    __tablename__ = "password_reset_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_email = Column(String(255), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    user = relationship("User", foreign_keys=[user_id])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by_user_id])
    school = relationship("School")

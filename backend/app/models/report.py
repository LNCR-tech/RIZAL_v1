from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.core.timezones import utc_now
from app.models.base import Base


class IssueReportType(Base):
    __tablename__ = "issue_report_types"

    code = Column(Text, primary_key=True)
    label = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class FeedbackCategory(Base):
    __tablename__ = "feedback_categories"

    code = Column(Text, primary_key=True)
    label = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class IssueReport(Base):
    __tablename__ = "issue_reports"

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reported_by = Column(Text, nullable=False)  # user email or "assistant"
    report_type_code = Column(Text, ForeignKey("issue_report_types.code", ondelete="RESTRICT"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="open")  # open, in_progress, resolved, closed
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    school = relationship("School")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    report_type = relationship("IssueReportType")


class UserFeedback(Base):
    __tablename__ = "user_feedbacks"

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    category_code = Column(Text, ForeignKey("feedback_categories.code", ondelete="RESTRICT"), nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    school = relationship("School")
    user = relationship("User", foreign_keys=[user_id])
    category = relationship("FeedbackCategory")

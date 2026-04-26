from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.timezones import utc_now
from app.models.base import Base


class BulkImportJob(Base):
    __tablename__ = "bulk_import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    target_school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), index=True, nullable=False)
    status = Column(Text, nullable=False, default="pending", index=True)
    original_filename = Column(Text, nullable=False)
    stored_file_path = Column(Text, nullable=False)
    failed_report_path = Column(Text, nullable=True)
    total_rows = Column(Integer, nullable=False, default=0)
    processed_rows = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    eta_seconds = Column(Integer, nullable=True)
    error_summary = Column(Text, nullable=True)
    is_rate_limited = Column(Boolean, nullable=False, default=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    errors = relationship("BulkImportError", back_populates="job", cascade="all, delete-orphan")


class BulkImportError(Base):
    __tablename__ = "bulk_import_errors"

    id = Column(BigInteger, primary_key=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("bulk_import_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    row_number = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    job = relationship("BulkImportJob", back_populates="errors")


class EmailDeliveryLog(Base):
    __tablename__ = "email_delivery_logs"

    id = Column(BigInteger, primary_key=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("bulk_import_jobs.id", ondelete="SET NULL"), index=True, nullable=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    email = Column(Text, nullable=False, index=True)
    status = Column(Text, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

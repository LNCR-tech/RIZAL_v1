"""Use: Defines database models for bulk import jobs and row errors.
Where to use: Use this when the backend needs to store or load bulk import jobs and row errors data.
Role: Model layer. It maps Python objects to database tables and relationships.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.models.base import Base


class BulkImportJob(Base):
    __tablename__ = "bulk_import_jobs"

    id = Column(String(36), primary_key=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    target_school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), index=True, nullable=False)

    status = Column(String(20), nullable=False, default="pending", index=True)
    original_filename = Column(String(255), nullable=False)
    stored_file_path = Column(String(1024), nullable=False)
    failed_report_path = Column(String(1024), nullable=True)

    total_rows = Column(Integer, nullable=False, default=0)
    processed_rows = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    eta_seconds = Column(Integer, nullable=True)

    error_summary = Column(Text, nullable=True)
    is_rate_limited = Column(Boolean, nullable=False, default=False)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_heartbeat = Column(DateTime, nullable=True)

    errors = relationship("BulkImportError", back_populates="job", cascade="all, delete-orphan")


class BulkImportError(Base):
    __tablename__ = "bulk_import_errors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("bulk_import_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    row_number = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=False)
    row_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    job = relationship("BulkImportJob", back_populates="errors")


class EmailDeliveryLog(Base):
    __tablename__ = "email_delivery_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("bulk_import_jobs.id", ondelete="SET NULL"), index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    email = Column(String(255), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

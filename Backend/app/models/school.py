from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    school_name = Column(String(255), nullable=False, index=True)
    school_code = Column(String(50), nullable=True, unique=True, index=True)
    address = Column(String(500), nullable=False)
    logo_url = Column(String(1000), nullable=True)
    primary_color = Column(String(7), nullable=False, default="#162F65")
    secondary_color = Column(String(7), nullable=True)
    subscription_status = Column(String(30), nullable=False, default="trial")
    active_status = Column(Boolean, nullable=False, default=True)
    subscription_plan = Column(String(100), nullable=False, default="free")
    subscription_start = Column(Date, nullable=False, default=date.today)
    subscription_end = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    settings = relationship(
        "SchoolSetting",
        back_populates="school",
        uselist=False,
        cascade="all, delete-orphan",
    )
    users = relationship("User", back_populates="school")
    student_profiles = relationship("StudentProfile", back_populates="school")
    events = relationship("Event", back_populates="school")
    audit_logs = relationship(
        "SchoolAuditLog",
        back_populates="school",
        cascade="all, delete-orphan",
    )


class SchoolSetting(Base):
    __tablename__ = "school_settings"

    school_id = Column(
        Integer,
        ForeignKey("schools.id", ondelete="CASCADE"),
        primary_key=True,
    )
    primary_color = Column(String(7), nullable=False, default="#162F65")
    secondary_color = Column(String(7), nullable=False, default="#2C5F9E")
    accent_color = Column(String(7), nullable=False, default="#4A90E2")
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    updated_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    school = relationship("School", back_populates="settings")


class SchoolAuditLog(Base):
    __tablename__ = "school_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(
        Integer,
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default="success")
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    school = relationship("School", back_populates="audit_logs")

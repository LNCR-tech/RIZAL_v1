"""Use: Defines database models for sanctions configuration, delegation, compliance, and clearance deadlines.
Where to use: Use this when the backend needs to store or load sanctions management data.
Role: Model layer. It maps Python objects to database tables and relationships.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.timezones import utc_now
from app.models.base import Base


class SanctionComplianceStatus(str, Enum):
    PENDING = "pending"
    COMPLIED = "complied"


class SanctionItemStatus(str, Enum):
    PENDING = "pending"
    COMPLIED = "complied"


class SanctionDelegationScopeType(str, Enum):
    UNIT = "unit"
    DEPARTMENT = "department"
    PROGRAM = "program"
    SCHOOL = "school"


class ClearanceDeadlineStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class EventSanctionConfig(Base):
    __tablename__ = "event_sanction_configs"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_event_sanction_configs_event_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    sanctions_enabled = Column(Boolean, nullable=False, default=False, index=True)
    item_definitions_json = Column(JSON, nullable=False, default=list)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    school = relationship("School")
    event = relationship("Event")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_user_id])
    sanction_records = relationship("SanctionRecord", back_populates="sanction_config")
    sanction_delegations = relationship("SanctionDelegation", back_populates="sanction_config")


class SanctionRecord(Base):
    __tablename__ = "sanction_records"
    __table_args__ = (
        UniqueConstraint("event_id", "student_profile_id", name="uq_sanction_records_event_student"),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    sanction_config_id = Column(
        Integer,
        ForeignKey("event_sanction_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    student_profile_id = Column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attendance_id = Column(Integer, ForeignKey("attendances.id", ondelete="SET NULL"), nullable=True, index=True)
    delegated_governance_unit_id = Column(
        Integer,
        ForeignKey("governance_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(
        SqlEnum(
            SanctionComplianceStatus,
            name="sanction_compliance_status",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=SanctionComplianceStatus.PENDING,
        index=True,
    )
    assigned_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    complied_at = Column(DateTime(timezone=True), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    school = relationship("School")
    event = relationship("Event")
    sanction_config = relationship("EventSanctionConfig", back_populates="sanction_records")
    student_profile = relationship("StudentProfile")
    attendance = relationship("Attendance")
    delegated_governance_unit = relationship("GovernanceUnit")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by_user_id])
    items = relationship("SanctionItem", back_populates="sanction_record", cascade="all, delete-orphan")
    compliance_history = relationship("SanctionComplianceHistory", back_populates="sanction_record")


class SanctionItem(Base):
    __tablename__ = "sanction_items"
    __table_args__ = (
        UniqueConstraint("sanction_record_id", "item_code", name="uq_sanction_items_record_item_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    sanction_record_id = Column(
        Integer,
        ForeignKey("sanction_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_code = Column(String(64), nullable=True, index=True)
    item_name = Column(String(255), nullable=False)
    item_description = Column(Text, nullable=True)
    status = Column(
        SqlEnum(
            SanctionItemStatus,
            name="sanction_item_status",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=SanctionItemStatus.PENDING,
        index=True,
    )
    complied_at = Column(DateTime(timezone=True), nullable=True, index=True)
    compliance_notes = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    sanction_record = relationship("SanctionRecord", back_populates="items")
    compliance_history = relationship("SanctionComplianceHistory", back_populates="sanction_item")


class SanctionDelegation(Base):
    __tablename__ = "sanction_delegations"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "delegated_to_governance_unit_id",
            name="uq_sanction_delegations_event_governance_unit",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    sanction_config_id = Column(
        Integer,
        ForeignKey("event_sanction_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delegated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    delegated_to_governance_unit_id = Column(
        Integer,
        ForeignKey("governance_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope_type = Column(
        SqlEnum(
            SanctionDelegationScopeType,
            name="sanction_delegation_scope_type",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=SanctionDelegationScopeType.UNIT,
        index=True,
    )
    scope_json = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    school = relationship("School")
    event = relationship("Event")
    sanction_config = relationship("EventSanctionConfig", back_populates="sanction_delegations")
    delegated_by_user = relationship("User", foreign_keys=[delegated_by_user_id])
    delegated_to_governance_unit = relationship("GovernanceUnit")
    revoked_by_user = relationship("User", foreign_keys=[revoked_by_user_id])


class SanctionComplianceHistory(Base):
    __tablename__ = "sanction_compliance_history"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    sanction_record_id = Column(
        Integer,
        ForeignKey("sanction_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sanction_item_id = Column(Integer, ForeignKey("sanction_items.id", ondelete="SET NULL"), nullable=True, index=True)
    student_profile_id = Column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    complied_on = Column(Date, nullable=False, default=date.today, index=True)
    school_year = Column(String(20), nullable=False, index=True)
    semester = Column(String(20), nullable=False, index=True)
    complied_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    school = relationship("School")
    event = relationship("Event")
    sanction_record = relationship("SanctionRecord", back_populates="compliance_history")
    sanction_item = relationship("SanctionItem", back_populates="compliance_history")
    student_profile = relationship("StudentProfile")
    complied_by_user = relationship("User", foreign_keys=[complied_by_user_id])


class ClearanceDeadline(Base):
    __tablename__ = "clearance_deadlines"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    declared_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_governance_unit_id = Column(
        Integer,
        ForeignKey("governance_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    deadline_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(
        SqlEnum(
            ClearanceDeadlineStatus,
            name="clearance_deadline_status",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=ClearanceDeadlineStatus.ACTIVE,
        index=True,
    )
    warning_email_sent_at = Column(DateTime(timezone=True), nullable=True)
    warning_popup_sent_at = Column(DateTime(timezone=True), nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    school = relationship("School")
    event = relationship("Event")
    declared_by_user = relationship("User", foreign_keys=[declared_by_user_id])
    target_governance_unit = relationship("GovernanceUnit")

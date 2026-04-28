from __future__ import annotations

from datetime import date
from enum import Enum

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint
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
        UniqueConstraint("event_id", name="event_sanction_configs_event_id_key"),
    )

    id = Column(BigInteger, primary_key=True)
    event_id = Column(BigInteger, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    sanctions_enabled = Column(Boolean, nullable=False, default=False, index=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    event = relationship("Event")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_user_id])
    sanction_records = relationship("SanctionRecord", back_populates="sanction_config")
    sanction_delegations = relationship("SanctionDelegation", back_populates="sanction_config")
    item_templates = relationship("SanctionItemTemplate", back_populates="sanction_config", cascade="all, delete-orphan")

    # Compatibility property — old code used item_definitions_json
    @property
    def item_definitions_json(self) -> list[dict]:
        return [
            {"item_code": t.item_code, "item_name": t.item_name, "item_description": t.item_description, "sort_order": t.sort_order}
            for t in sorted(self.item_templates, key=lambda x: x.sort_order)
        ]

    @item_definitions_json.setter
    def item_definitions_json(self, value: list[dict]) -> None:
        self.item_templates = [
            SanctionItemTemplate(
                item_code=item.get("item_code", ""),
                item_name=item.get("item_name", ""),
                item_description=item.get("item_description"),
                sort_order=item.get("sort_order", 0),
                is_required=item.get("is_required", True),
            )
            for item in (value or [])
        ]


class SanctionItemTemplate(Base):
    __tablename__ = "sanction_item_templates"
    __table_args__ = (
        UniqueConstraint("sanction_config_id", "item_code", name="sanction_item_templates_sanction_config_id_item_code_key"),
    )

    id = Column(BigInteger, primary_key=True)
    sanction_config_id = Column(BigInteger, ForeignKey("event_sanction_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    item_code = Column(Text, nullable=False)
    item_name = Column(Text, nullable=False)
    item_description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_required = Column(Boolean, nullable=False, default=True)

    sanction_config = relationship("EventSanctionConfig", back_populates="item_templates")


class SanctionRecord(Base):
    __tablename__ = "sanction_records"
    __table_args__ = (
        UniqueConstraint("event_id", "student_profile_id", name="sanction_records_event_id_student_profile_id_key"),
    )

    id = Column(BigInteger, primary_key=True)
    event_id = Column(BigInteger, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    student_profile_id = Column(BigInteger, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    sanction_config_id = Column(BigInteger, ForeignKey("event_sanction_configs.id", ondelete="SET NULL"), nullable=True, index=True)
    attendance_id = Column(BigInteger, ForeignKey("attendance_records.id", ondelete="SET NULL"), nullable=True, index=True)
    delegated_governance_unit_id = Column(BigInteger, ForeignKey("governance_units.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(Text, nullable=False, default=SanctionComplianceStatus.PENDING.value, index=True)
    assigned_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    complied_at = Column(DateTime(timezone=True), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    event = relationship("Event")
    sanction_config = relationship("EventSanctionConfig", back_populates="sanction_records")
    student_profile = relationship("StudentProfile")
    attendance = relationship("AttendanceRecord")
    delegated_governance_unit = relationship("GovernanceUnit")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by_user_id])
    items = relationship("SanctionRecordItem", back_populates="sanction_record", cascade="all, delete-orphan")
    compliance_history = relationship("SanctionComplianceHistory", back_populates="sanction_record")


class SanctionRecordItem(Base):
    __tablename__ = "sanction_record_items"
    __table_args__ = (
        UniqueConstraint("sanction_record_id", "item_code", name="sanction_record_items_sanction_record_id_item_code_key"),
    )

    id = Column(BigInteger, primary_key=True)
    sanction_record_id = Column(BigInteger, ForeignKey("sanction_records.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(BigInteger, ForeignKey("sanction_item_templates.id", ondelete="SET NULL"), nullable=True)
    item_code = Column(Text, nullable=True, index=True)
    item_name = Column(Text, nullable=False)
    item_description = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default=SanctionItemStatus.PENDING.value, index=True)
    complied_at = Column(DateTime(timezone=True), nullable=True, index=True)
    compliance_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    sanction_record = relationship("SanctionRecord", back_populates="items")
    compliance_history = relationship("SanctionComplianceHistory", back_populates="sanction_item")
    attributes = relationship("SanctionItemAttribute", back_populates="sanction_item", cascade="all, delete-orphan")


class SanctionItemAttribute(Base):
    __tablename__ = "sanction_item_attributes"

    sanction_record_item_id = Column(BigInteger, ForeignKey("sanction_record_items.id", ondelete="CASCADE"), primary_key=True)
    attribute_key = Column(Text, primary_key=True)
    attribute_value = Column(Text, nullable=True)

    sanction_item = relationship("SanctionRecordItem", back_populates="attributes")


# Compatibility alias — old code used SanctionItem
SanctionItem = SanctionRecordItem


class SanctionDelegation(Base):
    __tablename__ = "sanction_delegations"
    __table_args__ = (
        UniqueConstraint("event_id", "delegated_to_governance_unit_id", name="sanction_delegations_event_id_delegated_to_governance_unit_id_key"),
    )

    id = Column(BigInteger, primary_key=True)
    event_id = Column(BigInteger, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    sanction_config_id = Column(BigInteger, ForeignKey("event_sanction_configs.id", ondelete="SET NULL"), nullable=True, index=True)
    delegated_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    delegated_to_governance_unit_id = Column(BigInteger, ForeignKey("governance_units.id", ondelete="CASCADE"), nullable=False, index=True)
    scope_type = Column(Text, nullable=False, default=SanctionDelegationScopeType.UNIT.value, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    event = relationship("Event")
    sanction_config = relationship("EventSanctionConfig", back_populates="sanction_delegations")
    delegated_by_user = relationship("User", foreign_keys=[delegated_by_user_id])
    delegated_to_governance_unit = relationship("GovernanceUnit")
    revoked_by_user = relationship("User", foreign_keys=[revoked_by_user_id])
    scope_departments = relationship("SanctionDelegationDepartment", back_populates="delegation", cascade="all, delete-orphan")
    scope_programs = relationship("SanctionDelegationProgram", back_populates="delegation", cascade="all, delete-orphan")


class SanctionDelegationDepartment(Base):
    __tablename__ = "sanction_delegation_departments"

    delegation_id = Column(BigInteger, ForeignKey("sanction_delegations.id", ondelete="CASCADE"), primary_key=True)
    department_id = Column(BigInteger, ForeignKey("departments.id", ondelete="CASCADE"), primary_key=True)

    delegation = relationship("SanctionDelegation", back_populates="scope_departments")


class SanctionDelegationProgram(Base):
    __tablename__ = "sanction_delegation_programs"

    delegation_id = Column(BigInteger, ForeignKey("sanction_delegations.id", ondelete="CASCADE"), primary_key=True)
    program_id = Column(BigInteger, ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True)

    delegation = relationship("SanctionDelegation", back_populates="scope_programs")


class SanctionComplianceHistory(Base):
    __tablename__ = "sanction_compliance_history"

    id = Column(BigInteger, primary_key=True)
    sanction_record_id = Column(BigInteger, ForeignKey("sanction_records.id", ondelete="SET NULL"), nullable=True, index=True)
    sanction_record_item_id = Column(BigInteger, ForeignKey("sanction_record_items.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_period_id = Column(BigInteger, ForeignKey("academic_periods.id", ondelete="RESTRICT"), nullable=True, index=True)
    complied_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    compliance_term_label = Column(Text, nullable=False, default="")
    complied_on = Column(Date, nullable=False, default=date.today, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    sanction_record = relationship("SanctionRecord", back_populates="compliance_history")
    sanction_item = relationship("SanctionRecordItem", back_populates="compliance_history")
    academic_period = relationship("AcademicPeriod")
    complied_by_user = relationship("User", foreign_keys=[complied_by_user_id])


class AcademicPeriod(Base):
    __tablename__ = "academic_periods"
    __table_args__ = (
        UniqueConstraint("school_id", "school_year", "semester", name="academic_periods_school_id_school_year_semester_key"),
    )

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    school_year = Column(Text, nullable=False)
    semester = Column(Text, nullable=False)
    label = Column(Text, nullable=False)
    starts_on = Column(Date, nullable=True)
    ends_on = Column(Date, nullable=True)

    school = relationship("School")


class ClearanceDeadline(Base):
    __tablename__ = "clearance_deadlines"

    id = Column(BigInteger, primary_key=True)
    event_id = Column(BigInteger, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    declared_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_governance_unit_id = Column(BigInteger, ForeignKey("governance_units.id", ondelete="SET NULL"), nullable=True, index=True)
    deadline_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Text, nullable=False, default=ClearanceDeadlineStatus.ACTIVE.value, index=True)
    warning_email_sent_at = Column(DateTime(timezone=True), nullable=True)
    warning_popup_sent_at = Column(DateTime(timezone=True), nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    event = relationship("Event")
    declared_by_user = relationship("User", foreign_keys=[declared_by_user_id])
    target_governance_unit = relationship("GovernanceUnit")

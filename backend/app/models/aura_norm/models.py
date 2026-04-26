"""Subset of SQLAlchemy models for `aura_norm.*`.

These are intended for future incremental adoption. They are aligned to
`db_normalized/new_db_schema.sql`, but the running app continues to use the
current `public.*` models unless explicitly switched.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.aura_norm.base import AURA_NORM_SCHEMA, AuraNormBase


class SubscriptionPlan(AuraNormBase):
    __tablename__ = "subscription_plans"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    id = Column(BigInteger, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    display_name = Column(Text, nullable=False)
    user_limit = Column(Integer, nullable=False)
    event_limit_monthly = Column(Integer, nullable=False)
    import_limit_monthly = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class Role(AuraNormBase):
    __tablename__ = "roles"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    id = Column(BigInteger, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    display_name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class AttendanceStatus(AuraNormBase):
    __tablename__ = "attendance_statuses"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    code = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)


class AttendanceMethod(AuraNormBase):
    __tablename__ = "attendance_methods"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    code = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)


class NotificationChannel(AuraNormBase):
    __tablename__ = "notification_channels"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    code = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)
    supports_address = Column(Boolean, nullable=False, default=False)


class NotificationTopic(AuraNormBase):
    __tablename__ = "notification_topics"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    code = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)


class School(AuraNormBase):
    __tablename__ = "schools"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    id = Column(BigInteger, primary_key=True)
    school_code = Column(Text, unique=True)
    legal_name = Column(Text, nullable=False)
    display_name = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class User(AuraNormBase):
    __tablename__ = "users"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.schools.id", ondelete="CASCADE"))
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    prefix = Column(Text)
    first_name = Column(Text)
    middle_name = Column(Text)
    last_name = Column(Text)
    suffix = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    must_change_password = Column(Boolean, nullable=False, default=True)
    should_prompt_password_change = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    school = relationship("School")


class UserRole(AuraNormBase):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    user_id = Column(
        BigInteger,
        ForeignKey(f"{AURA_NORM_SCHEMA}.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id = Column(
        BigInteger,
        ForeignKey(f"{AURA_NORM_SCHEMA}.roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    assigned_at = Column(DateTime(timezone=True), nullable=False)
    assigned_by_user_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.users.id", ondelete="SET NULL"))

    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by_user_id])


class UserNotificationPreference(AuraNormBase):
    __tablename__ = "user_notification_preferences"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    user_id = Column(
        BigInteger,
        ForeignKey(f"{AURA_NORM_SCHEMA}.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    email_enabled = Column(Boolean, nullable=False, default=True)
    sms_enabled = Column(Boolean, nullable=False, default=False)
    sms_number = Column(Text)
    notify_missed_events = Column(Boolean, nullable=False, default=True)
    notify_low_attendance = Column(Boolean, nullable=False, default=True)
    notify_account_security = Column(Boolean, nullable=False, default=True)
    notify_subscription = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class Department(AuraNormBase):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("school_id", "name"), {"schema": AURA_NORM_SCHEMA})

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.schools.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)

    school = relationship("School")


class Program(AuraNormBase):
    __tablename__ = "programs"
    __table_args__ = (UniqueConstraint("school_id", "name"), {"schema": AURA_NORM_SCHEMA})

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.schools.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)

    school = relationship("School")


class AcademicPeriod(AuraNormBase):
    __tablename__ = "academic_periods"
    __table_args__ = (UniqueConstraint("school_id", "school_year", "semester"), {"schema": AURA_NORM_SCHEMA})

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.schools.id", ondelete="CASCADE"), nullable=False)
    school_year = Column(Text, nullable=False)
    semester = Column(Text, nullable=False)
    label = Column(Text, nullable=False)
    starts_on = Column(Date)
    ends_on = Column(Date)

    school = relationship("School")


class EventType(AuraNormBase):
    __tablename__ = "event_types"
    __table_args__ = (UniqueConstraint("school_id", "name"), {"schema": AURA_NORM_SCHEMA})

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.schools.id", ondelete="CASCADE"))
    name = Column(Text, nullable=False)
    code = Column(Text)
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class Event(AuraNormBase):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("end_at >= start_at", name="ck_events_end_after_start"),
        UniqueConstraint("created_by_user_id", "create_idempotency_key"),
        {"schema": AURA_NORM_SCHEMA},
    )

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.schools.id", ondelete="CASCADE"), nullable=False)
    event_type_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.event_types.id", ondelete="SET NULL"))
    created_by_user_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.users.id", ondelete="SET NULL"))
    create_idempotency_key = Column(Text)
    name = Column(Text, nullable=False)
    location = Column(Text)
    geo_latitude = Column(sa.Float)
    geo_longitude = Column(sa.Float)
    geo_radius_m = Column(sa.Float)
    geo_required = Column(Boolean, nullable=False, default=False)
    geo_max_accuracy_m = Column(sa.Float)
    early_check_in_minutes = Column(Integer, nullable=False)
    late_threshold_minutes = Column(Integer, nullable=False)
    sign_out_grace_minutes = Column(Integer, nullable=False)
    sign_out_open_delay_minutes = Column(Integer, nullable=False, default=0)
    sign_out_override_until = Column(DateTime(timezone=True))
    present_until_override_at = Column(DateTime(timezone=True))
    late_until_override_at = Column(DateTime(timezone=True))
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class AttendanceRecord(AuraNormBase):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("student_profile_id", "event_id"), {"schema": AURA_NORM_SCHEMA})

    id = Column(BigInteger, primary_key=True)
    student_profile_id = Column(BigInteger, nullable=False)
    event_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.events.id", ondelete="CASCADE"), nullable=False)
    time_in = Column(DateTime(timezone=True), nullable=False)
    time_out = Column(DateTime(timezone=True))
    method_code = Column(Text, ForeignKey(f"{AURA_NORM_SCHEMA}.attendance_methods.code", ondelete="RESTRICT"), nullable=False)
    status_code = Column(Text, ForeignKey(f"{AURA_NORM_SCHEMA}.attendance_statuses.code", ondelete="RESTRICT"), nullable=False)
    verified_by_user_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.users.id", ondelete="SET NULL"))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class GovernanceUnit(AuraNormBase):
    __tablename__ = "governance_units"
    __table_args__ = (UniqueConstraint("school_id", "unit_code"), {"schema": AURA_NORM_SCHEMA})

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.schools.id", ondelete="CASCADE"), nullable=False)
    parent_unit_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.governance_units.id", ondelete="SET NULL"))
    unit_code = Column(Text, nullable=False)
    unit_name = Column(Text, nullable=False)
    description = Column(Text)
    unit_type = Column(Text, nullable=False)
    created_by_user_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.users.id", ondelete="SET NULL"))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class GovernancePermission(AuraNormBase):
    __tablename__ = "governance_permissions"
    __table_args__ = {"schema": AURA_NORM_SCHEMA}

    id = Column(BigInteger, primary_key=True)
    permission_code = Column(Text, nullable=False, unique=True)
    permission_name = Column(Text, nullable=False)
    description = Column(Text)


class GovernanceMember(AuraNormBase):
    __tablename__ = "governance_members"
    __table_args__ = (UniqueConstraint("governance_unit_id", "user_id"), {"schema": AURA_NORM_SCHEMA})

    id = Column(BigInteger, primary_key=True)
    governance_unit_id = Column(
        BigInteger,
        ForeignKey(f"{AURA_NORM_SCHEMA}.governance_units.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.users.id", ondelete="CASCADE"), nullable=False)
    position_title = Column(Text)
    assigned_by_user_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.users.id", ondelete="SET NULL"))
    assigned_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class SanctionItemTemplate(AuraNormBase):
    __tablename__ = "sanction_item_templates"
    __table_args__ = (UniqueConstraint("sanction_config_id", "item_code"), {"schema": AURA_NORM_SCHEMA})

    id = Column(BigInteger, primary_key=True)
    sanction_config_id = Column(BigInteger, nullable=False)
    item_code = Column(Text, nullable=False)
    item_name = Column(Text, nullable=False)
    item_description = Column(Text)
    sort_order = Column(Integer, nullable=False, default=0)
    is_required = Column(Boolean, nullable=False, default=True)


class SanctionRecord(AuraNormBase):
    __tablename__ = "sanction_records"
    __table_args__ = (UniqueConstraint("event_id", "student_profile_id"), {"schema": AURA_NORM_SCHEMA})

    id = Column(BigInteger, primary_key=True)
    event_id = Column(BigInteger, ForeignKey(f"{AURA_NORM_SCHEMA}.events.id", ondelete="CASCADE"), nullable=False)
    student_profile_id = Column(BigInteger, nullable=False)
    status = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

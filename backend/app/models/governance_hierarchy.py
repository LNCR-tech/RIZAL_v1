from __future__ import annotations

from enum import Enum

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.core.timezones import utc_now
from app.models.base import Base


class GovernanceUnitType(str, Enum):
    SSG = "SSG"
    SG = "SG"
    ORG = "ORG"


class PermissionCode(str, Enum):
    CREATE_SG = "create_sg"
    CREATE_ORG = "create_org"
    MANAGE_STUDENTS = "manage_students"
    VIEW_STUDENTS = "view_students"
    MANAGE_MEMBERS = "manage_members"
    MANAGE_EVENTS = "manage_events"
    MANAGE_ATTENDANCE = "manage_attendance"
    MANAGE_ANNOUNCEMENTS = "manage_announcements"
    ASSIGN_PERMISSIONS = "assign_permissions"
    VIEW_SANCTIONED_STUDENTS_LIST = "view_sanctioned_students_list"
    VIEW_STUDENT_SANCTION_DETAIL = "view_student_sanction_detail"
    APPROVE_SANCTION_COMPLIANCE = "approve_sanction_compliance"
    CONFIGURE_EVENT_SANCTIONS = "configure_event_sanctions"
    EXPORT_SANCTIONED_STUDENTS = "export_sanctioned_students"
    VIEW_SANCTIONS_DASHBOARD = "view_sanctions_dashboard"


class GovernanceAnnouncementStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


PERMISSION_DEFINITIONS: dict[PermissionCode, dict[str, str]] = {
    PermissionCode.CREATE_SG: {"permission_name": "Create SG", "description": "Allows members of the unit to create SG child units."},
    PermissionCode.CREATE_ORG: {"permission_name": "Create ORG", "description": "Allows members of the unit to create ORG child units."},
    PermissionCode.MANAGE_STUDENTS: {"permission_name": "Manage Students", "description": "Allows members of the unit to manage students within their allowed scope."},
    PermissionCode.VIEW_STUDENTS: {"permission_name": "View Students", "description": "Allows members of the unit to view students within their allowed scope."},
    PermissionCode.MANAGE_MEMBERS: {"permission_name": "Manage Members", "description": "Allows members of the unit to manage governance memberships."},
    PermissionCode.MANAGE_EVENTS: {"permission_name": "Manage Events", "description": "Allows members of the unit to manage events within their allowed scope."},
    PermissionCode.MANAGE_ATTENDANCE: {"permission_name": "Manage Attendance", "description": "Allows members of the unit to manage attendance within their allowed scope."},
    PermissionCode.MANAGE_ANNOUNCEMENTS: {"permission_name": "Manage Announcements", "description": "Allows members of the unit to publish and manage announcements."},
    PermissionCode.ASSIGN_PERMISSIONS: {"permission_name": "Assign Permissions", "description": "Allows members of the unit to assign governance permissions."},
    PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST: {"permission_name": "View Sanctioned Students List", "description": "Allows members of the unit to view sanctioned students lists for accessible events."},
    PermissionCode.VIEW_STUDENT_SANCTION_DETAIL: {"permission_name": "View Student Sanction Detail", "description": "Allows members of the unit to view detailed sanction records for accessible students."},
    PermissionCode.APPROVE_SANCTION_COMPLIANCE: {"permission_name": "Approve Sanction Compliance", "description": "Allows members of the unit to mark student sanctions as complied for accessible events."},
    PermissionCode.CONFIGURE_EVENT_SANCTIONS: {"permission_name": "Configure Event Sanctions", "description": "Allows members of the unit to configure event sanctions, delegation, and clearance deadline actions."},
    PermissionCode.EXPORT_SANCTIONED_STUDENTS: {"permission_name": "Export Sanctioned Students", "description": "Allows members of the unit to export sanctioned student records for accessible events."},
    PermissionCode.VIEW_SANCTIONS_DASHBOARD: {"permission_name": "View Sanctions Dashboard", "description": "Allows members of the unit to view sanctions dashboard summaries for accessible events."},
}


class GovernanceUnit(Base):
    __tablename__ = "governance_units"
    __table_args__ = (
        UniqueConstraint("school_id", "unit_code", name="governance_units_school_id_unit_code_key"),
    )

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_unit_id = Column(BigInteger, ForeignKey("governance_units.id", ondelete="SET NULL"), nullable=True, index=True)
    unit_code = Column(Text, nullable=False, index=True)
    unit_name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    unit_type = Column(Text, nullable=False, index=True)
    department_id = Column(BigInteger, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    program_id = Column(BigInteger, ForeignKey("programs.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    event_default_early_check_in_minutes = Column(Integer, nullable=True)
    event_default_late_threshold_minutes = Column(Integer, nullable=True)
    event_default_sign_out_grace_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    parent_unit = relationship("GovernanceUnit", remote_side=[id], back_populates="child_units")
    child_units = relationship("GovernanceUnit", back_populates="parent_unit")
    members = relationship("GovernanceMember", back_populates="governance_unit", cascade="all, delete-orphan")
    unit_permissions = relationship("GovernanceUnitPermission", back_populates="governance_unit", cascade="all, delete-orphan")
    announcements = relationship("GovernanceAnnouncement", back_populates="governance_unit", cascade="all, delete-orphan")
    student_notes = relationship("GovernanceStudentNote", back_populates="governance_unit", cascade="all, delete-orphan")
    school = relationship("School")
    department = relationship("Department")
    program = relationship("Program")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])


class GovernanceMember(Base):
    __tablename__ = "governance_members"
    __table_args__ = (
        UniqueConstraint("governance_unit_id", "user_id", name="governance_members_governance_unit_id_user_id_key"),
    )

    id = Column(BigInteger, primary_key=True)
    governance_unit_id = Column(BigInteger, ForeignKey("governance_units.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    position_title = Column(Text, nullable=True)
    assigned_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    governance_unit = relationship("GovernanceUnit", back_populates="members")
    member_permissions = relationship("GovernanceMemberPermission", back_populates="governance_member", cascade="all, delete-orphan")
    user = relationship("User", foreign_keys=[user_id])
    assigned_by_user = relationship("User", foreign_keys=[assigned_by_user_id])


class GovernancePermission(Base):
    __tablename__ = "governance_permissions"

    id = Column(BigInteger, primary_key=True)
    permission_code = Column(Text, nullable=False, unique=True, index=True)
    permission_name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    unit_permissions = relationship("GovernanceUnitPermission", back_populates="permission")
    member_permissions = relationship("GovernanceMemberPermission", back_populates="permission")


class GovernanceUnitPermission(Base):
    __tablename__ = "governance_unit_permissions"

    governance_unit_id = Column(BigInteger, ForeignKey("governance_units.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(BigInteger, ForeignKey("governance_permissions.id", ondelete="CASCADE"), primary_key=True)
    granted_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    governance_unit = relationship("GovernanceUnit", back_populates="unit_permissions")
    permission = relationship("GovernancePermission", back_populates="unit_permissions")
    granted_by_user = relationship("User", foreign_keys=[granted_by_user_id])

    # Compatibility alias
    @property
    def created_at(self):
        return self.granted_at


class GovernanceMemberPermission(Base):
    __tablename__ = "governance_member_permissions"

    governance_member_id = Column(BigInteger, ForeignKey("governance_members.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(BigInteger, ForeignKey("governance_permissions.id", ondelete="CASCADE"), primary_key=True)
    granted_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    governance_member = relationship("GovernanceMember", back_populates="member_permissions")
    permission = relationship("GovernancePermission", back_populates="member_permissions")
    granted_by_user = relationship("User", foreign_keys=[granted_by_user_id])

    @property
    def created_at(self):
        return self.granted_at


class GovernanceAnnouncement(Base):
    __tablename__ = "governance_announcements"

    id = Column(BigInteger, primary_key=True)
    governance_unit_id = Column(BigInteger, ForeignKey("governance_units.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default=GovernanceAnnouncementStatus.DRAFT.value, index=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    governance_unit = relationship("GovernanceUnit", back_populates="announcements")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_user_id])

    @hybrid_property
    def school_id(self):
        return self.governance_unit.school_id if self.governance_unit else None

    @school_id.expression
    def school_id(cls):
        from app.models.governance_hierarchy import GovernanceUnit
        return GovernanceUnit.school_id

    @school_id.setter
    def school_id(self, value):
        pass  # school_id is derived from governance_unit; ignore direct assignment

    @property
    def author_name(self) -> str | None:
        author = self.updated_by_user or self.created_by_user
        if author is None:
            return None
        name_parts = [author.first_name, author.last_name]
        full_name = " ".join(p.strip() for p in name_parts if p and p.strip()).strip()
        return full_name or author.email


class GovernanceStudentNote(Base):
    __tablename__ = "governance_student_notes"
    __table_args__ = (
        UniqueConstraint("governance_unit_id", "student_profile_id", name="governance_student_notes_governance_unit_id_student_profile_id_key"),
    )

    id = Column(BigInteger, primary_key=True)
    governance_unit_id = Column(BigInteger, ForeignKey("governance_units.id", ondelete="CASCADE"), nullable=False, index=True)
    student_profile_id = Column(BigInteger, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    notes = Column(Text, nullable=False, default="")
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    governance_unit = relationship("GovernanceUnit", back_populates="student_notes")
    student_profile = relationship("StudentProfile")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_user_id])
    tag_entries = relationship("GovernanceStudentNoteTag", back_populates="note", cascade="all, delete-orphan")

    # Compatibility property — old code used note.tags as a JSON list
    @property
    def tags(self) -> list[str]:
        return [t.tag for t in self.tag_entries]


class GovernanceStudentNoteTag(Base):
    __tablename__ = "governance_student_note_tags"

    note_id = Column(BigInteger, ForeignKey("governance_student_notes.id", ondelete="CASCADE"), primary_key=True)
    tag = Column(Text, nullable=False, primary_key=True)

    note = relationship("GovernanceStudentNote", back_populates="tag_entries")

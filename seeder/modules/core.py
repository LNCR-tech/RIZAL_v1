import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import database models
from app.core.database import engine
from app.models.base import Base
from app.models.school import School, SchoolBranding, SchoolEventPolicy
from app.models.department import Department
from app.models.program import Program
from app.models.user import User, UserRole, StudentProfile
from app.models.role import Role
from app.models.governance_hierarchy import (
    GovernanceUnit, GovernanceMember, GovernancePermission,
    GovernanceUnitPermission, GovernanceMemberPermission, GovernanceUnitType,
    GovernanceAnnouncement, GovernanceStudentNote,
    PERMISSION_DEFINITIONS
)
from app.models.event import Event, EventStatus
from app.models.event_type import EventType
from app.models.governance_hierarchy import GovernanceAnnouncementStatus
from app.models.sanctions import (
    EventSanctionConfig, SanctionRecord, SanctionItem, SanctionDelegation,
    SanctionComplianceStatus, SanctionItemStatus, SanctionDelegationScopeType,
    SanctionComplianceHistory
)

from modules.data import DEFAULT_ROLES, DEFAULT_ROLE_NAMES

logger = logging.getLogger(__name__)

def ensure_tables() -> None:
    """Creates all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def wipe_records(db: Session, preserve_platform_admin: str = None) -> None:
    """
    Deletes seeded records in a high-performance FK-safe manner using TRUNCATE.
    If preserve_platform_admin email is provided, we surgically delete other users.
    """
    logger.info("Wiping existing database records... (Bulk Truncate Mode)")
    
    # Core Data Tables (Ordered for safety, though CASCADE handles the tree)
    tables_to_truncate = [
        "sanction_compliance_history",
        "sanction_record_items",
        "sanction_records",
        "sanction_delegations",
        "event_sanction_configs",
        "attendance_records",
        "event_departments",
        "event_programs",
        "events",
        "governance_member_permissions",
        "governance_members",
        "governance_unit_permissions",
        "governance_student_notes",
        "governance_announcements",
        "governance_units",
        "student_profiles",
        "user_roles",
        "programs",
        "departments",
        "school_audit_logs",
        "school_branding",
        "school_event_policies",
        "schools"
    ]
    
    # Execute high-speed bulk truncate
    table_str = ", ".join(tables_to_truncate)
    db.execute(text(f"TRUNCATE TABLE {table_str} CASCADE"))
        
    if preserve_platform_admin:
        # Delete users except the platform admin (TRUNCATE doesn't support WHERE)
        db.execute(text("DELETE FROM users WHERE email != :email"), {"email": preserve_platform_admin})
    else:
        db.execute(text("TRUNCATE TABLE users CASCADE"))
    
    db.commit()
    logger.info("Database wiped.")

def seed_roles(db: Session) -> None:
    """Seed the 3 real platform roles (admin, campus_admin, student)."""
    for role_def in DEFAULT_ROLES:
        role = db.query(Role).filter(Role.code == role_def["name"]).first()
        if not role:
            db.add(Role(code=role_def["name"], display_name=role_def["display_name"]))
    db.commit()

def seed_permission_catalog(db: Session) -> None:
    for code, details in PERMISSION_DEFINITIONS.items():
        perm = db.query(GovernancePermission).filter(GovernancePermission.permission_code == code).first()
        if not perm:
            perm = GovernancePermission(
                permission_code=code,
                permission_name=details["permission_name"],
                description=details["description"]
            )
            db.add(perm)
    db.commit()

def seed_platform_admin(db: Session, email: str, password_hash: str) -> User:
    admin = db.query(User).filter(User.email == email).first()
    if not admin:
        admin = User(
            email=email,
            password_hash=password_hash,
            first_name="Platform",
            last_name="Admin",
            is_active=True,
            must_change_password=False
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if admin_role:
        role_link = db.query(UserRole).filter_by(user_id=admin.id, role_id=admin_role.id).first()
        if not role_link:
            db.add(UserRole(user_id=admin.id, role_id=admin_role.id))
            db.commit()

    return admin

def get_or_create_school(db: Session, **kwargs) -> School:
    school_display = kwargs.get("school_name", kwargs.get("name", ""))
    school = db.query(School).filter(School.display_name == school_display).first()
    if not school:
        school = School(
            legal_name=kwargs.get("name", school_display),
            display_name=school_display,
            school_code=kwargs.get("school_code"),
            address=kwargs.get("address", "123 Default St"),
        )
        db.add(school)
        db.flush()

        # Colors live in school_branding, not on the School row itself
        branding = SchoolBranding(
            school_id=school.id,
            primary_color=kwargs.get("primary_color", "#162F65"),
            secondary_color=kwargs.get("secondary_color", "#2C5F9E"),
            accent_color=kwargs.get("accent_color", "#4A90E2"),
        )
        db.add(branding)

        # Event policy row (no color columns — just defaults)
        db.add(SchoolEventPolicy(school_id=school.id))

        db.commit()
        db.refresh(school)
    return school

def get_or_create_department(db: Session, school_id: int, name: str) -> Department:
    dept = db.query(Department).filter_by(school_id=school_id, name=name).first()
    if not dept:
        dept = Department(school_id=school_id, name=name)
        db.add(dept)
        db.commit()
        db.refresh(dept)
    return dept

def get_or_create_program(db: Session, school_id: int, name: str) -> Program:
    prog = db.query(Program).filter_by(school_id=school_id, name=name).first()
    if not prog:
        prog = Program(school_id=school_id, name=name)
        db.add(prog)
        db.commit()
        db.refresh(prog)
    return prog

def link_program_to_department(db: Session, program: Program, department: Department):
    if program not in department.programs:
        department.programs.append(program)
        db.commit()

def create_user(db: Session, **kwargs) -> User:
    user = User(
        email=kwargs["email"],
        school_id=kwargs.get("school_id"),
        password_hash=kwargs["password_hash"],
        first_name=kwargs["first_name"],
        middle_name=kwargs.get("middle_name"),
        last_name=kwargs["last_name"],
        suffix=kwargs.get("suffix"),
        is_active=True,
        must_change_password=False,
        should_prompt_password_change=False
    )
    db.add(user)
    db.flush()
    return user

def assign_role(db: Session, user: User, role_name: str) -> None:
    role = db.query(Role).filter(Role.code == role_name).first()
    if role:
        from app.models.user import UserRole
        existing = db.query(UserRole).filter_by(user_id=user.id, role_id=role.id).first()
        if not existing:
            db.add(UserRole(user_id=user.id, role_id=role.id))
            db.flush()

def create_student_profile(db: Session, **kwargs) -> StudentProfile:
    profile = StudentProfile(
        user_id=kwargs["user_id"],
        school_id=kwargs["school_id"],
        student_number=kwargs["student_id"],  # normalized column name
        department_id=kwargs.get("department_id"),
        program_id=kwargs.get("program_id"),
        year_level=kwargs.get("year_level", 1)
    )
    db.add(profile)
    db.flush()
    return profile

def create_governance_unit(db: Session, **kwargs) -> GovernanceUnit:
    raw_type = kwargs["unit_type"]
    unit = GovernanceUnit(
        school_id=kwargs["school_id"],
        unit_code=kwargs["unit_code"],
        unit_name=kwargs["unit_name"],
        unit_type=raw_type.value if hasattr(raw_type, "value") else raw_type,
        parent_unit_id=kwargs.get("parent_id"),
        department_id=kwargs.get("department_id"),
        program_id=kwargs.get("program_id")
    )
    db.add(unit)
    db.flush()
    return unit

def assign_unit_permissions(db: Session, unit_id: int, permission_codes: list) -> None:
    perms = db.query(GovernancePermission).filter(GovernancePermission.permission_code.in_(permission_codes)).all()
    for perm in perms:
        db.add(GovernanceUnitPermission(governance_unit_id=unit_id, permission_id=perm.id))
    db.flush()

def create_governance_member(db: Session, unit_id: int, user_id: int, position_title: str) -> GovernanceMember:
    mem = GovernanceMember(governance_unit_id=unit_id, user_id=user_id, position_title=position_title)
    db.add(mem)
    db.flush()
    return mem

def set_member_permissions(db: Session, member_id: int, permission_codes: list) -> None:
    perms = db.query(GovernancePermission).filter(GovernancePermission.permission_code.in_(permission_codes)).all()
    for perm in perms:
        db.add(GovernanceMemberPermission(governance_member_id=member_id, permission_id=perm.id))
    db.flush()

def resolve_event_type_id(db: Session, event_type_name: str) -> int | None:
    """Resolve an EventType name to its ID, checking global types first then any school type."""
    et = db.query(EventType).filter(
        EventType.name == event_type_name,
        EventType.school_id.is_(None)
    ).first()
    if et is None:
        et = db.query(EventType).filter(EventType.name == event_type_name).first()
    return et.id if et else None

def create_event(db: Session, **kwargs) -> Event:
    event_type_id = None
    if kwargs.get("event_type"):
        event_type_id = resolve_event_type_id(db, kwargs["event_type"])
    raw_status = kwargs.get("status", EventStatus.UPCOMING)
    event = Event(
        school_id=kwargs["school_id"],
        name=kwargs["name"],
        location=kwargs["location"],
        start_at=kwargs["start_dt"],
        end_at=kwargs["end_dt"],
        status=raw_status.value if hasattr(raw_status, "value") else raw_status,
        event_type_id=event_type_id
    )
    db.add(event)
    db.flush()
    return event

def create_sanction_config(db: Session, **kwargs) -> EventSanctionConfig:
    # item_definitions_json no longer exists in normalized schema — config is template-based
    conf = EventSanctionConfig(
        event_id=kwargs["event_id"],
        sanctions_enabled=True,
    )
    db.add(conf)
    db.flush()
    return conf

def create_sanction_delegation(db: Session, **kwargs) -> SanctionDelegation:
    raw_scope = kwargs["scope_type"]
    dele = SanctionDelegation(
        event_id=kwargs["event_id"],
        sanction_config_id=kwargs["config_id"],
        delegated_to_governance_unit_id=kwargs["unit_id"],
        scope_type=raw_scope.value if hasattr(raw_scope, "value") else raw_scope
    )
    db.add(dele)
    db.flush()
    return dele

def create_sanction_record(db: Session, **kwargs) -> SanctionRecord:
    raw_status = SanctionComplianceStatus.PENDING
    rec = SanctionRecord(
        event_id=kwargs["event_id"],
        sanction_config_id=kwargs.get("config_id"),
        student_profile_id=kwargs["student_profile_id"],
        attendance_id=kwargs["attendance_id"],
        delegated_governance_unit_id=kwargs.get("delegated_unit_id"),
        status=raw_status.value if hasattr(raw_status, "value") else raw_status
    )
    db.add(rec)
    db.flush()
    return rec

def create_sanction_item(db: Session, record_id: int, item_code: str, item_name: str) -> None:
    raw_status = SanctionItemStatus.PENDING
    item = SanctionItem(
        sanction_record_id=record_id,
        item_code=item_code,
        item_name=item_name,
        status=raw_status.value if hasattr(raw_status, "value") else raw_status
    )
    db.add(item)
    db.flush()

def create_announcement(db: Session, **kwargs) -> GovernanceAnnouncement:
    raw_status = kwargs.get("status", GovernanceAnnouncementStatus.PUBLISHED)
    ann = GovernanceAnnouncement(
        governance_unit_id=kwargs["unit_id"],
        title=kwargs["title"],
        body=kwargs["body"],
        status=raw_status.value if hasattr(raw_status, "value") else raw_status,
        created_by_user_id=kwargs.get("created_by")
    )
    db.add(ann)
    db.flush()
    return ann

def create_student_note(db: Session, **kwargs) -> GovernanceStudentNote:
    note = GovernanceStudentNote(
        governance_unit_id=kwargs["unit_id"],
        student_profile_id=kwargs["student_id"],
        notes=kwargs["notes"],
        created_by_user_id=kwargs.get("created_by")
    )
    db.add(note)
    db.flush()
    return note

def create_compliance_history(db: Session, **kwargs) -> SanctionComplianceHistory:
    history = SanctionComplianceHistory(
        sanction_record_id=kwargs.get("record_id"),
        sanction_record_item_id=kwargs.get("item_id"),
        complied_by_user_id=kwargs.get("complied_by"),
        academic_period_id=kwargs.get("academic_period_id"),
        compliance_term_label=kwargs.get("compliance_term_label", ""),
        notes=kwargs.get("notes")
    )
    db.add(history)
    db.flush()
    return history

def seed_event_types(db: Session) -> None:
    """Seed global event types by delegating to the backend's own seeder."""
    from app.seeder import seed_event_types as _backend_seed_event_types
    _backend_seed_event_types(db)
    logger.info("Event types seeded.")


def seed_attendance_statuses(db: Session) -> None:
    """Seed the required attendance_statuses lookup rows."""
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(db.bind)
    if "attendance_statuses" not in inspector.get_table_names():
        logger.warning("attendance_statuses table not found — skipping status seed.")
        return

    statuses = [
        {"code": "present",  "display_name": "Present"},
        {"code": "late",     "display_name": "Late"},
        {"code": "absent",   "display_name": "Absent"},
        {"code": "excused",  "display_name": "Excused"},
    ]
    existing = {row[0] for row in db.execute(text("SELECT code FROM attendance_statuses")).fetchall()}
    for s in statuses:
        if s["code"] not in existing:
            db.execute(
                text("INSERT INTO attendance_statuses (code, display_name) VALUES (:code, :display_name)"),
                {"code": s["code"], "display_name": s["display_name"]}
            )
    db.commit()
    logger.info("Attendance statuses seeded.")


def seed_attendance_methods(db: Session) -> None:
    """Seed the required attendance_methods lookup rows.
    
    attendance_records.method_code is a NOT NULL FK to attendance_methods.code.
    Without at least 'manual' existing, attendance inserts will fail.
    """
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(db.bind)
    if "attendance_methods" not in inspector.get_table_names():
        logger.warning("attendance_methods table not found — skipping method seed.")
        return

    methods = [
        {"code": "manual",  "display_name": "Manual Entry"},
        {"code": "rfid",    "display_name": "RFID Tap"},
        {"code": "face",    "display_name": "Face Recognition"},
        {"code": "qr",      "display_name": "QR Code Scan"},
    ]
    existing = {row[0] for row in db.execute(text("SELECT code FROM attendance_methods")).fetchall()}
    for m in methods:
        if m["code"] not in existing:
            db.execute(
                text("INSERT INTO attendance_methods (code, display_name) VALUES (:code, :display_name)"),
                {"code": m["code"], "display_name": m["display_name"]}
            )
    db.commit()
    logger.info("Attendance methods seeded.")

"""Role- and permission-based policy rules for MCP schema/query services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


def normalize_role(role: str) -> str:
    return (role or "").strip().lower().replace(" ", "_")


def normalize_permission(permission: str) -> str:
    return (permission or "").strip().lower()


@dataclass(frozen=True)
class AccessPolicy:
    allowed_tables: set[str]
    allowed_columns: dict[str, set[str]]
    required_filters: dict[str, set[str]]  # table -> direct filter columns
    scope_notes: dict[str, str]  # table -> text rule when direct filters are not enough
    allowed_write_tables: set[str]
    capability_notes: tuple[str, ...]
    non_capability_notes: tuple[str, ...]


EMPTY_POLICY = AccessPolicy(
    allowed_tables=set(),
    allowed_columns={},
    required_filters={},
    scope_notes={},
    allowed_write_tables=set(),
    capability_notes=(),
    non_capability_notes=(),
)


SAFE_USER_COLUMNS = {
    "id",
    "email",
    "school_id",
    "first_name",
    "middle_name",
    "last_name",
    "is_active",
    "must_change_password",
    "should_prompt_password_change",
    "created_at",
}

SAFE_STUDENT_PROFILE_COLUMNS = {
    "id",
    "user_id",
    "school_id",
    "student_id",
    "department_id",
    "program_id",
    "year_level",
    "is_face_registered",
    "face_image_url",
    "registration_complete",
    "section",
    "last_face_update",
}

SANCTIONS_TABLES = {
    "event_sanction_configs",
    "sanction_records",
    "sanction_items",
    "sanction_delegations",
    "sanction_compliance_history",
    "clearance_deadlines",
}

SANCTIONS_SCHOOL_SCOPED_TABLES = {
    "event_sanction_configs",
    "sanction_records",
    "sanction_delegations",
    "sanction_compliance_history",
    "clearance_deadlines",
}


BASE_ROLE_POLICIES: dict[str, AccessPolicy] = {
    "admin": AccessPolicy(
        allowed_tables={
            "users",
            "roles",
            "user_roles",
            "schools",
            "school_settings",
            "school_subscription_settings",
            "school_subscription_reminders",
            "departments",
            "programs",
            "events",
            "attendances",
            "student_profiles",
            "governance_units",
            "governance_members",
            "governance_member_permissions",
            "governance_permissions",
            "governance_announcements",
            "governance_student_notes",
            "data_governance_settings",
            "data_requests",
            "data_retention_run_logs",
            "notification_logs",
            "school_audit_logs",
            "login_history",
            *SANCTIONS_TABLES,
        },
        allowed_columns={
            "users": set(SAFE_USER_COLUMNS),
            "student_profiles": set(SAFE_STUDENT_PROFILE_COLUMNS),
        },
        required_filters={},
        scope_notes={},
        allowed_write_tables={
            "users",
            "schools",
            "school_settings",
            "school_subscription_settings",
            "school_subscription_reminders",
            "departments",
            "programs",
            "events",
            "attendances",
            "student_profiles",
            "governance_units",
            "governance_members",
            "governance_member_permissions",
            "governance_announcements",
            "governance_student_notes",
            "data_governance_settings",
            "data_requests",
        },
        capability_notes=(
            "Can manage school-wide users, settings, subscriptions, events, attendance, and governance data.",
            "Can inspect and update governance units, memberships, permissions, announcements, and notes.",
            "Can manage universities, colleges/departments, programs, and bulk student import through dedicated tools.",
        ),
        non_capability_notes=(
            "Cannot run DELETE or DDL through MCP.",
        ),
    ),
    "campus_admin": AccessPolicy(
        allowed_tables={
            "users",
            "schools",
            "school_settings",
            "school_subscription_settings",
            "school_subscription_reminders",
            "departments",
            "programs",
            "events",
            "attendances",
            "student_profiles",
            "governance_units",
            "governance_members",
            "governance_member_permissions",
            "governance_permissions",
            "governance_announcements",
            "governance_student_notes",
            "data_governance_settings",
            "data_requests",
            "data_retention_run_logs",
            "notification_logs",
            "school_audit_logs",
            "login_history",
            *SANCTIONS_TABLES,
        },
        allowed_columns={
            "users": set(SAFE_USER_COLUMNS),
            "student_profiles": set(SAFE_STUDENT_PROFILE_COLUMNS),
        },
        required_filters={
            "users": {"school_id"},
            "schools": {"id"},
            "school_settings": {"school_id"},
            "school_subscription_settings": {"school_id"},
            "school_subscription_reminders": {"school_id"},
            "departments": {"school_id"},
            "programs": {"school_id"},
            "events": {"school_id"},
            "student_profiles": {"school_id"},
            "governance_units": {"school_id"},
            "governance_announcements": {"school_id"},
            "governance_student_notes": {"school_id"},
            "data_governance_settings": {"school_id"},
            "data_requests": {"school_id"},
            "data_retention_run_logs": {"school_id"},
            "notification_logs": {"school_id"},
            "school_audit_logs": {"school_id"},
            "login_history": {"school_id"},
            "event_sanction_configs": {"school_id"},
            "sanction_records": {"school_id"},
            "sanction_delegations": {"school_id"},
            "sanction_compliance_history": {"school_id"},
            "clearance_deadlines": {"school_id"},
        },
        scope_notes={
            "attendances": "Must stay inside the current school by joining events.school_id or student_profiles.school_id.",
            "governance_members": "Must stay inside the current school by joining governance_units.school_id.",
            "governance_member_permissions": "Must stay inside the current school by joining governance_members -> governance_units.school_id.",
            "governance_permissions": "Read the global governance permission catalog only; do not mutate the catalog itself.",
            "sanction_items": "Must stay inside the current school by joining sanction_records.school_id.",
        },
        allowed_write_tables={
            "users",
            "school_settings",
            "school_subscription_settings",
            "school_subscription_reminders",
            "departments",
            "programs",
            "events",
            "attendances",
            "student_profiles",
            "governance_units",
            "governance_members",
            "governance_member_permissions",
            "governance_announcements",
            "governance_student_notes",
            "data_governance_settings",
            "data_requests",
        },
        capability_notes=(
            "Can manage school-scoped students, settings, subscriptions, governance hierarchy, reports, attendance, and announcement monitoring.",
            "Can bootstrap SSG and manage school-scoped governance data.",
            "Can manage the current university profile, colleges/departments, programs, and bulk student import inside the current school.",
        ),
        non_capability_notes=(
            "Must stay inside the current school.",
            "Should not promote or modify admin or campus_admin accounts through assistant actions.",
            "Cannot manage other universities outside the current school.",
            "Cannot enumerate all schools system-wide; can only access the current school's profile.",
        ),
    ),
    "student": AccessPolicy(
        allowed_tables={
            "departments",
            "events",
            "attendances",
            "student_profiles",
            "governance_announcements",
            "sanction_records",
            "sanction_items",
            "sanction_compliance_history",
            "clearance_deadlines",
        },
        allowed_columns={
            "student_profiles": set(SAFE_STUDENT_PROFILE_COLUMNS),
        },
        required_filters={
            "departments": {"school_id"},
            "events": {"school_id"},
            "student_profiles": {"school_id", "user_id"},
            "governance_announcements": {"school_id"},
            "sanction_records": {"school_id"},
            "sanction_compliance_history": {"school_id"},
            "clearance_deadlines": {"school_id"},
        },
        scope_notes={
            "events": "Normal student event access is limited to school-wide events plus the student's own department and program scope.",
            "attendances": "Must resolve the caller's own student_profiles.id from user_id and only inspect that student's attendance records.",
            "sanction_records": "Must resolve the caller's own student_profiles.id from user_id and only inspect sanction records for that student profile.",
            "sanction_items": "Must stay limited to sanction items that belong to the caller's own sanction records.",
            "sanction_compliance_history": "Must resolve the caller's own student_profiles.id from user_id and only inspect compliance history for that student profile.",
        },
        allowed_write_tables=set(),
        capability_notes=(
            "Can read in-scope events, own attendance-derived records, own sanctions and compliance history, own student profile context, and school colleges/departments.",
        ),
        non_capability_notes=(
            "Without additional governance permissions, cannot manage governance data, users, school settings, or write tenant data.",
            "Cannot bulk import students or manage universities, departments, or programs.",
        ),
    ),
    "ssg": AccessPolicy(
        allowed_tables={"departments", "governance_units"},
        allowed_columns={
            "users": set(SAFE_USER_COLUMNS),
            "student_profiles": set(SAFE_STUDENT_PROFILE_COLUMNS),
        },
        required_filters={
            "departments": {"school_id"},
            "governance_units": {"school_id"},
        },
        scope_notes={
            "governance_units": "SSG membership alone does not unlock features; officer permissions determine actual access.",
        },
        allowed_write_tables=set(),
        capability_notes=(
            "Active SSG membership is recognized, but real features depend on officer permission codes.",
            "Can read the colleges/departments available in the current school.",
        ),
        non_capability_notes=(
            "Do not assume SSG can manage events, attendance, students, announcements, members, or permissions without explicit grants.",
        ),
    ),
    "sg": AccessPolicy(
        allowed_tables={"departments", "governance_units"},
        allowed_columns={
            "users": set(SAFE_USER_COLUMNS),
            "student_profiles": set(SAFE_STUDENT_PROFILE_COLUMNS),
        },
        required_filters={
            "departments": {"school_id"},
            "governance_units": {"school_id"},
        },
        scope_notes={
            "governance_units": "SG membership alone does not unlock features; officer permissions determine actual access.",
        },
        allowed_write_tables=set(),
        capability_notes=(
            "Active SG membership is recognized, but real features depend on officer permission codes.",
            "Can read the colleges/departments available in the current school.",
        ),
        non_capability_notes=(
            "Do not assume SG can manage events, attendance, students, announcements, members, or permissions without explicit grants.",
        ),
    ),
    "org": AccessPolicy(
        allowed_tables={"departments", "governance_units"},
        allowed_columns={},
        required_filters={
            "departments": {"school_id"},
            "governance_units": {"school_id"},
        },
        scope_notes={
            "governance_units": "ORG membership alone does not unlock features; officer permissions determine actual access.",
        },
        allowed_write_tables=set(),
        capability_notes=(
            "Active ORG membership is recognized, but real features depend on officer permission codes.",
            "Can read the colleges/departments available in the current school.",
        ),
        non_capability_notes=(
            "Do not assume ORG can manage events, attendance, students, announcements, members, or permissions without explicit grants.",
        ),
    ),
}


PERMISSION_POLICIES: dict[str, AccessPolicy] = {
    "create_sg": AccessPolicy(
        allowed_tables={"governance_units", "departments", "programs"},
        allowed_columns={},
        required_filters={
            "governance_units": {"school_id"},
            "departments": {"school_id"},
            "programs": {"school_id"},
        },
        scope_notes={
            "governance_units": "SSG officers with create_sg can create or edit department-scoped SG units inside their school only.",
        },
        allowed_write_tables={"governance_units"},
        capability_notes=("Can create and edit SG units within allowed school scope.",),
        non_capability_notes=(),
    ),
    "create_org": AccessPolicy(
        allowed_tables={"governance_units", "departments", "programs"},
        allowed_columns={},
        required_filters={
            "governance_units": {"school_id"},
            "departments": {"school_id"},
            "programs": {"school_id"},
        },
        scope_notes={
            "governance_units": "SG officers with create_org can create or edit ORG units only inside the parent department/program scope.",
        },
        allowed_write_tables={"governance_units"},
        capability_notes=("Can create and edit ORG units within the parent SG scope.",),
        non_capability_notes=(),
    ),
    "view_students": AccessPolicy(
        allowed_tables={"users", "student_profiles", "governance_student_notes", "departments", "programs"},
        allowed_columns={},
        required_filters={
            "users": {"school_id"},
            "student_profiles": {"school_id"},
            "governance_student_notes": {"school_id"},
            "departments": {"school_id"},
            "programs": {"school_id"},
        },
        scope_notes={
            "users": "Governance student visibility must stay inside the caller's allowed school/department/program scope.",
            "student_profiles": "Governance student visibility must stay inside the caller's allowed school/department/program scope.",
            "governance_student_notes": "Notes must stay inside the same governance unit scope as the caller.",
        },
        allowed_write_tables=set(),
        capability_notes=("Can search and view students within the governance unit scope.",),
        non_capability_notes=(),
    ),
    "manage_students": AccessPolicy(
        allowed_tables={"users", "student_profiles", "governance_student_notes", "departments", "programs"},
        allowed_columns={},
        required_filters={
            "users": {"school_id"},
            "student_profiles": {"school_id"},
            "governance_student_notes": {"school_id"},
            "departments": {"school_id"},
            "programs": {"school_id"},
        },
        scope_notes={
            "users": "Governance student management must stay inside the caller's allowed school/department/program scope.",
            "student_profiles": "Governance student management must stay inside the caller's allowed school/department/program scope.",
            "governance_student_notes": "Only governance_student_notes are writable; do not update base user roles or admin-owned profile fields.",
        },
        allowed_write_tables={"governance_student_notes"},
        capability_notes=("Can view students in scope and create or update governance student notes.",),
        non_capability_notes=("Cannot directly rewrite protected user/account role data through governance student management.",),
    ),
    "manage_members": AccessPolicy(
        allowed_tables={"governance_members", "governance_units", "users", "student_profiles"},
        allowed_columns={},
        required_filters={
            "governance_units": {"school_id"},
            "users": {"school_id"},
            "student_profiles": {"school_id"},
        },
        scope_notes={
            "governance_members": "Must stay inside the allowed governance unit scope and parent-child management rules.",
        },
        allowed_write_tables={"governance_members"},
        capability_notes=("Can assign, update, reactivate, and deactivate governance members in allowed child-unit scope.",),
        non_capability_notes=(),
    ),
    "manage_events": AccessPolicy(
        allowed_tables={"events", "governance_units", "school_settings", "departments", "programs"},
        allowed_columns={},
        required_filters={
            "events": {"school_id"},
            "governance_units": {"school_id"},
            "school_settings": {"school_id"},
            "departments": {"school_id"},
            "programs": {"school_id"},
        },
        scope_notes={
            "events": "Governance event management must stay inside the caller's school/department/program governance scope.",
        },
        allowed_write_tables={"events"},
        capability_notes=("Can create, update, and monitor events in allowed governance scope.",),
        non_capability_notes=(),
    ),
    "view_sanctioned_students_list": AccessPolicy(
        allowed_tables={
            "sanction_records",
            "sanction_items",
            "event_sanction_configs",
            "sanction_delegations",
            "events",
            "student_profiles",
            "users",
            "governance_units",
            "departments",
            "programs",
        },
        allowed_columns={
            "users": set(SAFE_USER_COLUMNS),
            "student_profiles": set(SAFE_STUDENT_PROFILE_COLUMNS),
        },
        required_filters={
            "sanction_records": {"school_id"},
            "event_sanction_configs": {"school_id"},
            "sanction_delegations": {"school_id"},
            "events": {"school_id"},
            "student_profiles": {"school_id"},
            "users": {"school_id"},
            "governance_units": {"school_id"},
            "departments": {"school_id"},
            "programs": {"school_id"},
        },
        scope_notes={
            "sanction_records": "Must stay inside the caller's governance event scope and delegation visibility rules.",
            "sanction_items": "Must stay inside sanction_records visible to the caller's governance event scope.",
        },
        allowed_write_tables=set(),
        capability_notes=("Can read sanctioned-student lists for allowed governance scope.",),
        non_capability_notes=("Sanctions MCP access is read-only; compliance approval is not allowed through MCP.",),
    ),
    "view_student_sanction_detail": AccessPolicy(
        allowed_tables={
            "sanction_records",
            "sanction_items",
            "sanction_compliance_history",
            "event_sanction_configs",
            "events",
            "student_profiles",
            "users",
            "governance_units",
            "departments",
            "programs",
        },
        allowed_columns={
            "users": set(SAFE_USER_COLUMNS),
            "student_profiles": set(SAFE_STUDENT_PROFILE_COLUMNS),
        },
        required_filters={
            "sanction_records": {"school_id"},
            "sanction_compliance_history": {"school_id"},
            "event_sanction_configs": {"school_id"},
            "events": {"school_id"},
            "student_profiles": {"school_id"},
            "users": {"school_id"},
            "governance_units": {"school_id"},
            "departments": {"school_id"},
            "programs": {"school_id"},
        },
        scope_notes={
            "sanction_records": "Must stay inside the caller's governance event scope and delegation visibility rules.",
            "sanction_items": "Must stay inside sanction_records visible to the caller's governance event scope.",
            "sanction_compliance_history": "Must stay inside the same sanctions visibility scope as sanction_records.",
        },
        allowed_write_tables=set(),
        capability_notes=("Can read detailed sanction records and item-level compliance for scoped students.",),
        non_capability_notes=("Sanctions MCP access is read-only; compliance approval is not allowed through MCP.",),
    ),
    "approve_sanction_compliance": AccessPolicy(
        allowed_tables={
            "sanction_records",
            "sanction_items",
            "sanction_compliance_history",
            "event_sanction_configs",
            "sanction_delegations",
            "events",
            "student_profiles",
            "users",
            "governance_units",
        },
        allowed_columns={
            "users": set(SAFE_USER_COLUMNS),
            "student_profiles": set(SAFE_STUDENT_PROFILE_COLUMNS),
        },
        required_filters={
            "sanction_records": {"school_id"},
            "sanction_compliance_history": {"school_id"},
            "event_sanction_configs": {"school_id"},
            "sanction_delegations": {"school_id"},
            "events": {"school_id"},
            "student_profiles": {"school_id"},
            "users": {"school_id"},
            "governance_units": {"school_id"},
        },
        scope_notes={
            "sanction_records": "Must stay inside the caller's governance event scope and delegation visibility rules.",
            "sanction_items": "Must stay inside sanction_records visible to the caller's governance event scope.",
        },
        allowed_write_tables=set(),
        capability_notes=("Can inspect sanction compliance state for decisions inside allowed governance scope.",),
        non_capability_notes=("Sanctions MCP access is read-only; sanction approvals must run through backend API routes, not MCP writes.",),
    ),
    "configure_event_sanctions": AccessPolicy(
        allowed_tables={
            "event_sanction_configs",
            "sanction_delegations",
            "clearance_deadlines",
            "events",
            "governance_units",
            "departments",
            "programs",
            "sanction_records",
            "sanction_items",
        },
        allowed_columns={},
        required_filters={
            "event_sanction_configs": {"school_id"},
            "sanction_delegations": {"school_id"},
            "clearance_deadlines": {"school_id"},
            "events": {"school_id"},
            "governance_units": {"school_id"},
            "departments": {"school_id"},
            "programs": {"school_id"},
            "sanction_records": {"school_id"},
        },
        scope_notes={
            "event_sanction_configs": "Must stay inside events visible to the caller's governance ownership/delegation scope.",
            "sanction_delegations": "Must stay inside events visible to the caller's governance ownership/delegation scope.",
            "sanction_items": "Must stay inside sanction_records visible to the caller's governance scope.",
        },
        allowed_write_tables=set(),
        capability_notes=("Can inspect event sanction setup, delegation, and clearance deadlines in allowed governance scope.",),
        non_capability_notes=("Sanctions MCP access is read-only; sanction configuration and delegation updates are not allowed through MCP writes.",),
    ),
    "export_sanctioned_students": AccessPolicy(
        allowed_tables={
            "sanction_records",
            "sanction_items",
            "sanction_compliance_history",
            "events",
            "student_profiles",
            "users",
            "departments",
            "programs",
            "governance_units",
        },
        allowed_columns={
            "users": set(SAFE_USER_COLUMNS),
            "student_profiles": set(SAFE_STUDENT_PROFILE_COLUMNS),
        },
        required_filters={
            "sanction_records": {"school_id"},
            "sanction_compliance_history": {"school_id"},
            "events": {"school_id"},
            "student_profiles": {"school_id"},
            "users": {"school_id"},
            "departments": {"school_id"},
            "programs": {"school_id"},
            "governance_units": {"school_id"},
        },
        scope_notes={
            "sanction_records": "Export visibility must stay inside the caller's governance event scope and delegation rules.",
            "sanction_items": "Must stay inside sanction_records visible to the caller's governance scope.",
        },
        allowed_write_tables=set(),
        capability_notes=("Can read sanction export data for allowed governance scope.",),
        non_capability_notes=("Sanctions MCP access is read-only; no export metadata writes are allowed through MCP.",),
    ),
    "view_sanctions_dashboard": AccessPolicy(
        allowed_tables={
            "sanction_records",
            "sanction_items",
            "event_sanction_configs",
            "sanction_delegations",
            "sanction_compliance_history",
            "clearance_deadlines",
            "events",
            "governance_units",
            "student_profiles",
            "users",
        },
        allowed_columns={
            "users": set(SAFE_USER_COLUMNS),
            "student_profiles": set(SAFE_STUDENT_PROFILE_COLUMNS),
        },
        required_filters={
            "sanction_records": {"school_id"},
            "event_sanction_configs": {"school_id"},
            "sanction_delegations": {"school_id"},
            "sanction_compliance_history": {"school_id"},
            "clearance_deadlines": {"school_id"},
            "events": {"school_id"},
            "governance_units": {"school_id"},
            "student_profiles": {"school_id"},
            "users": {"school_id"},
        },
        scope_notes={
            "sanction_records": "Dashboard metrics must stay inside the caller's governance event scope and delegation rules.",
            "sanction_items": "Must stay inside sanction_records visible to the caller's governance scope.",
        },
        allowed_write_tables=set(),
        capability_notes=("Can read sanctions dashboard metrics and compliance snapshots in allowed governance scope.",),
        non_capability_notes=("Sanctions MCP access is read-only; dashboard actions that mutate data are not allowed through MCP.",),
    ),
    "manage_attendance": AccessPolicy(
        allowed_tables={"attendances", "events", "student_profiles"},
        allowed_columns={},
        required_filters={
            "events": {"school_id"},
            "student_profiles": {"school_id"},
        },
        scope_notes={
            "attendances": "Attendance operations must stay inside the caller's allowed event scope and student scope.",
        },
        allowed_write_tables={"attendances"},
        capability_notes=("Can read attendance reports and manage attendance within allowed governance scope.",),
        non_capability_notes=(),
    ),
    "manage_announcements": AccessPolicy(
        allowed_tables={"governance_announcements", "governance_units"},
        allowed_columns={},
        required_filters={
            "governance_announcements": {"school_id"},
            "governance_units": {"school_id"},
        },
        scope_notes={
            "governance_announcements": "Announcements must stay inside the selected governance unit scope.",
        },
        allowed_write_tables={"governance_announcements"},
        capability_notes=("Can list, create, update, publish, archive, and delete governance announcements within allowed unit scope.",),
        non_capability_notes=(),
    ),
    "assign_permissions": AccessPolicy(
        allowed_tables={
            "governance_member_permissions",
            "governance_permissions",
            "governance_members",
            "governance_units",
        },
        allowed_columns={},
        required_filters={
            "governance_units": {"school_id"},
        },
        scope_notes={
            "governance_member_permissions": "Permission assignment must stay inside the caller's allowed governance unit scope.",
            "governance_members": "Permission changes target governance members only; do not alter base auth roles.",
            "governance_permissions": "Read from the governance permission catalog; do not mutate the catalog.",
        },
        allowed_write_tables={"governance_member_permissions"},
        capability_notes=("Can inspect permission grants and assign governance permissions within allowed unit scope.",),
        non_capability_notes=(),
    ),
}


ROLE_PRIORITY = ["admin", "campus_admin", "ssg", "sg", "org", "student"]


def merge_policies(policies: Sequence[AccessPolicy]) -> AccessPolicy:
    if not policies:
        return EMPTY_POLICY

    allowed_tables: set[str] = set()
    allowed_columns: dict[str, set[str]] = {}
    required_filters: dict[str, set[str]] = {}
    scope_notes: dict[str, str] = {}
    allowed_write_tables: set[str] = set()
    capability_notes: list[str] = []
    non_capability_notes: list[str] = []

    for policy in policies:
        allowed_tables.update(policy.allowed_tables)
        allowed_write_tables.update(policy.allowed_write_tables)

        for table, columns in policy.allowed_columns.items():
            allowed_columns.setdefault(table, set()).update(columns)

        for table, filters in policy.required_filters.items():
            required_filters.setdefault(table, set()).update(filters)

        for table, note in policy.scope_notes.items():
            if table not in scope_notes:
                scope_notes[table] = note

        for note in policy.capability_notes:
            if note not in capability_notes:
                capability_notes.append(note)

        for note in policy.non_capability_notes:
            if note not in non_capability_notes:
                non_capability_notes.append(note)

    return AccessPolicy(
        allowed_tables=allowed_tables,
        allowed_columns=allowed_columns,
        required_filters=required_filters,
        scope_notes=scope_notes,
        allowed_write_tables=allowed_write_tables,
        capability_notes=tuple(capability_notes),
        non_capability_notes=tuple(non_capability_notes),
    )


def get_effective_policy(
    roles: Iterable[str],
    permissions: Iterable[str] | None = None,
) -> AccessPolicy:
    normalized_roles = {normalize_role(role) for role in roles if normalize_role(role)}
    normalized_permissions = {
        normalize_permission(permission)
        for permission in (permissions or [])
        if normalize_permission(permission)
    }

    policies: list[AccessPolicy] = [
        BASE_ROLE_POLICIES[role]
        for role in ROLE_PRIORITY
        if role in normalized_roles
    ]

    for permission in sorted(normalized_permissions):
        policy = PERMISSION_POLICIES.get(permission)
        if policy:
            policies.append(policy)

    if not policies:
        return EMPTY_POLICY

    return merge_policies(policies)


def get_policy(role: str) -> AccessPolicy:
    return get_effective_policy([role], [])


def filter_allowed_tables(policy: AccessPolicy, tables: Iterable[str]) -> list[str]:
    return [table for table in tables if table in policy.allowed_tables]


def filter_allowed_columns(policy: AccessPolicy, table: str, columns: Iterable[str]) -> list[str]:
    allowed = policy.allowed_columns.get(table)
    if not allowed:
        return list(columns)
    return [column for column in columns if column in allowed]


def summarize_scope_rules(policy: AccessPolicy) -> list[str]:
    table_names = sorted(policy.allowed_tables)
    summary: list[str] = []
    for table_name in table_names:
        direct_filters = policy.required_filters.get(table_name, set())
        scope_note = policy.scope_notes.get(table_name)
        if direct_filters:
            summary.append(f"{table_name}: direct filters -> {', '.join(sorted(direct_filters))}")
        elif scope_note:
            summary.append(f"{table_name}: {scope_note}")
    return summary

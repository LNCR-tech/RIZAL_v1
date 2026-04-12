"""Dedicated school, department, and program management MCP service."""

from __future__ import annotations

from datetime import date
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from policy import (
    AccessPolicy,
    get_effective_policy,
    normalize_permission,
    normalize_role,
)


TENANT_DATABASE_URL = (
    os.getenv("TENANT_DATABASE_URL")
    or os.getenv("APP_DATABASE_URL")
    or os.getenv("DATABASE_URL")
)

DEFAULT_PRIMARY_COLOR = "#162F65"
DEFAULT_SECONDARY_COLOR = "#2C5F9E"
DEFAULT_ACCENT_COLOR = "#4A90E2"
DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES = 30
DEFAULT_EVENT_LATE_THRESHOLD_MINUTES = 10
DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES = 20

if not TENANT_DATABASE_URL:
    raise RuntimeError("TENANT_DATABASE_URL (or APP_DATABASE_URL/DATABASE_URL) is required.")

engine = create_engine(TENANT_DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="MCP School Admin Service")


class ActionRequest(BaseModel):
    role: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    school_id: int | None = None
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)


def _resolve_roles(body: ActionRequest) -> list[str]:
    combined = [*body.roles]
    if body.role:
        combined.append(body.role)

    normalized: list[str] = []
    seen = set()
    for role in combined:
        normalized_role = normalize_role(role)
        if not normalized_role or normalized_role in seen:
            continue
        seen.add(normalized_role)
        normalized.append(normalized_role)
    return normalized


def _resolve_permissions(body: ActionRequest) -> list[str]:
    normalized: list[str] = []
    seen = set()
    for permission in body.permissions:
        normalized_permission = normalize_permission(permission)
        if not normalized_permission or normalized_permission in seen:
            continue
        seen.add(normalized_permission)
        normalized.append(normalized_permission)
    return normalized


def _resolve_policy(body: ActionRequest) -> tuple[list[str], list[str], AccessPolicy]:
    roles = _resolve_roles(body)
    if not roles:
        raise HTTPException(status_code=400, detail="role or roles are required")
    permissions = _resolve_permissions(body)
    return roles, permissions, get_effective_policy(roles, permissions)


def _is_admin(roles: list[str]) -> bool:
    return "admin" in roles


def _is_campus_admin(roles: list[str]) -> bool:
    return "campus_admin" in roles


def _require_admin(roles: list[str]) -> None:
    if not _is_admin(roles):
        raise HTTPException(status_code=403, detail="admin role required")


def _require_school_admin(roles: list[str]) -> None:
    if not (_is_admin(roles) or _is_campus_admin(roles)):
        raise HTTPException(status_code=403, detail="admin or campus_admin role required")


def _require_table_read(policy: AccessPolicy, table: str) -> None:
    if table not in policy.allowed_tables:
        raise HTTPException(status_code=403, detail=f"read access denied for table: {table}")


def _require_table_write(policy: AccessPolicy, table: str) -> None:
    if table not in policy.allowed_write_tables:
        raise HTTPException(status_code=403, detail=f"write access denied for table: {table}")


def _require_school_scope(body: ActionRequest, payload: dict[str, Any], *, allow_admin_none: bool = False) -> int | None:
    requested_school_id = payload.get("school_id", body.school_id)
    roles = _resolve_roles(body)

    if _is_admin(roles):
        if requested_school_id is None and not allow_admin_none:
            raise HTTPException(status_code=400, detail="school_id is required for this action")
        return int(requested_school_id) if requested_school_id is not None else None

    if body.school_id is None:
        raise HTTPException(status_code=400, detail="school_id is required for school-scoped actions")

    if requested_school_id is not None and int(requested_school_id) != int(body.school_id):
        raise HTTPException(status_code=403, detail="school scope mismatch")

    return int(body.school_id)


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text_value = str(value).strip().lower()
    if text_value in {"true", "1", "yes", "y", "on"}:
        return True
    if text_value in {"false", "0", "no", "n", "off"}:
        return False
    raise HTTPException(status_code=400, detail=f"invalid boolean value: {value}")


def _coerce_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid date value: {value}") from exc


def _fetch_school(conn, school_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        text(
            """
            select
                s.id,
                s.name,
                s.school_name,
                s.school_code,
                s.address,
                s.logo_url,
                s.primary_color,
                s.secondary_color,
                s.subscription_status,
                s.active_status,
                s.subscription_plan,
                s.subscription_start,
                s.subscription_end,
                s.created_at,
                s.updated_at,
                ss.event_default_early_check_in_minutes,
                ss.event_default_late_threshold_minutes,
                ss.event_default_sign_out_grace_minutes
            from schools s
            left join school_settings ss on ss.school_id = s.id
            where s.id = :school_id
            """
        ),
        {"school_id": school_id},
    ).mappings().first()
    return dict(row) if row else None


def _fetch_department(conn, department_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        text(
            """
            select id, school_id, name
            from departments
            where id = :department_id
            """
        ),
        {"department_id": department_id},
    ).mappings().first()
    return dict(row) if row else None


def _fetch_program(conn, program_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        text(
            """
            select
                p.id,
                p.school_id,
                p.name,
                coalesce(
                    array_agg(pda.department_id order by pda.department_id)
                    filter (where pda.department_id is not null),
                    '{}'
                ) as department_ids
            from programs p
            left join program_department_association pda on pda.program_id = p.id
            where p.id = :program_id
            group by p.id
            """
        ),
        {"program_id": program_id},
    ).mappings().first()
    if not row:
        return None
    program = dict(row)
    program["department_ids"] = list(program.get("department_ids") or [])
    return program


def _validate_department_ids(conn, school_id: int, department_ids: list[int]) -> None:
    if not department_ids:
        return
    rows = conn.execute(
        text(
            """
            select id
            from departments
            where school_id = :school_id
              and id = any(:department_ids)
            """
        ),
        {"school_id": school_id, "department_ids": department_ids},
    ).fetchall()
    found_ids = {int(row[0]) for row in rows}
    missing_ids = sorted(set(department_ids) - found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"department ids do not belong to school {school_id}: {missing_ids}",
        )


def _program_rows(conn, school_id: int | None = None) -> list[dict[str, Any]]:
    if school_id is None:
        where_sql = ""
        params: dict[str, Any] = {}
    else:
        where_sql = "where p.school_id = :school_id"
        params = {"school_id": school_id}

    rows = conn.execute(
        text(
            f"""
            select
                p.id,
                p.school_id,
                p.name,
                coalesce(
                    array_agg(pda.department_id order by pda.department_id)
                    filter (where pda.department_id is not null),
                    '{{}}'
                ) as department_ids
            from programs p
            left join program_department_association pda on pda.program_id = p.id
            {where_sql}
            group by p.id
            order by p.school_id nulls first, p.name asc
            """
        ),
        params,
    ).mappings().all()
    serialized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["department_ids"] = list(item.get("department_ids") or [])
        serialized.append(item)
    return serialized


def _event_rows(
    conn,
    *,
    school_id: int | None,
    status: str | None = None,
    upcoming_only: bool = False,
    limit: int = 20,
) -> list[dict[str, Any]]:
    where_parts: list[str] = []
    params: dict[str, Any] = {"limit": max(1, min(limit, 100))}
    if school_id is not None:
        where_parts.append("school_id = :school_id")
        params["school_id"] = school_id
    if status:
        where_parts.append("status = :status")
        params["status"] = status
    if upcoming_only:
        where_parts.append("start_datetime >= current_timestamp")
    where_sql = f"where {' and '.join(where_parts)}" if where_parts else ""
    rows = conn.execute(
        text(
            f"""
            select
                id,
                school_id,
                name,
                location,
                start_datetime,
                end_datetime,
                status
            from events
            {where_sql}
            order by start_datetime asc
            limit :limit
            """
        ),
        params,
    ).mappings().all()
    return [dict(row) for row in rows]


def _run_action_internal(body: ActionRequest) -> dict[str, Any]:
    roles, _permissions, policy = _resolve_policy(body)
    action = body.action.strip().lower()
    payload = body.payload or {}

    with engine.begin() as conn:
        if action == "list_schools":
            # Admin can list all schools. Campus admin can only see their own school.
            if _is_admin(roles):
                rows = conn.execute(
                    text(
                        """
                        select
                            id,
                            school_name,
                            school_code,
                            address,
                            primary_color,
                            secondary_color,
                            subscription_status,
                            active_status,
                            subscription_plan,
                            subscription_start,
                            subscription_end,
                            created_at,
                            updated_at
                        from schools
                        order by school_name asc
                        """
                    )
                ).mappings().all()
                return {"action": action, "count": len(rows), "rows": [dict(row) for row in rows]}

            if _is_campus_admin(roles):
                if body.school_id is None:
                    raise HTTPException(status_code=400, detail="school_id is required for campus_admin list_schools")
                row = conn.execute(
                    text(
                        """
                        select
                            id,
                            school_name,
                            school_code,
                            address,
                            primary_color,
                            secondary_color,
                            subscription_status,
                            active_status,
                            subscription_plan,
                            subscription_start,
                            subscription_end,
                            created_at,
                            updated_at
                        from schools
                        where id = :school_id
                        """
                    ),
                    {"school_id": int(body.school_id)},
                ).mappings().first()
                rows = [dict(row)] if row else []
                return {"action": action, "count": len(rows), "rows": rows}

            raise HTTPException(status_code=403, detail="admin or campus_admin role required")

        if action == "get_school":
            _require_school_admin(roles)
            school_id = _require_school_scope(body, payload)
            school = _fetch_school(conn, int(school_id))
            if not school:
                raise HTTPException(status_code=404, detail="school not found")
            return {"action": action, "school": school}

        if action == "create_school":
            _require_admin(roles)

            school_name = _normalize_optional_text(payload.get("school_name"))
            if not school_name:
                raise HTTPException(status_code=400, detail="payload.school_name is required")

            school_code = _normalize_optional_text(payload.get("school_code"))
            address = _normalize_optional_text(payload.get("address")) or f"{school_name} Address"
            logo_url = _normalize_optional_text(payload.get("logo_url"))
            primary_color = _normalize_optional_text(payload.get("primary_color")) or DEFAULT_PRIMARY_COLOR
            secondary_color = _normalize_optional_text(payload.get("secondary_color")) or DEFAULT_SECONDARY_COLOR
            subscription_status = _normalize_optional_text(payload.get("subscription_status")) or "trial"
            subscription_plan = _normalize_optional_text(payload.get("subscription_plan")) or "free"
            active_status = _coerce_bool(payload.get("active_status"))
            if active_status is None:
                active_status = True
            subscription_start = _coerce_date(payload.get("subscription_start")) or date.today()
            subscription_end = _coerce_date(payload.get("subscription_end"))

            inserted = conn.execute(
                text(
                    """
                    insert into schools (
                        name,
                        school_name,
                        school_code,
                        address,
                        logo_url,
                        primary_color,
                        secondary_color,
                        subscription_status,
                        active_status,
                        subscription_plan,
                        subscription_start,
                        subscription_end
                    )
                    values (
                        :name,
                        :school_name,
                        :school_code,
                        :address,
                        :logo_url,
                        :primary_color,
                        :secondary_color,
                        :subscription_status,
                        :active_status,
                        :subscription_plan,
                        :subscription_start,
                        :subscription_end
                    )
                    returning id
                    """
                ),
                {
                    "name": school_name,
                    "school_name": school_name,
                    "school_code": school_code,
                    "address": address,
                    "logo_url": logo_url,
                    "primary_color": primary_color,
                    "secondary_color": secondary_color,
                    "subscription_status": subscription_status,
                    "active_status": active_status,
                    "subscription_plan": subscription_plan,
                    "subscription_start": subscription_start,
                    "subscription_end": subscription_end,
                },
            ).scalar_one()

            conn.execute(
                text(
                    """
                    insert into school_settings (
                        school_id,
                        primary_color,
                        secondary_color,
                        accent_color,
                        event_default_early_check_in_minutes,
                        event_default_late_threshold_minutes,
                        event_default_sign_out_grace_minutes
                    )
                    values (
                        :school_id,
                        :primary_color,
                        :secondary_color,
                        :accent_color,
                        :early,
                        :late,
                        :sign_out
                    )
                    """
                ),
                {
                    "school_id": inserted,
                    "primary_color": primary_color,
                    "secondary_color": secondary_color,
                    "accent_color": secondary_color or primary_color or DEFAULT_ACCENT_COLOR,
                    "early": int(payload.get("event_default_early_check_in_minutes") or DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES),
                    "late": int(payload.get("event_default_late_threshold_minutes") or DEFAULT_EVENT_LATE_THRESHOLD_MINUTES),
                    "sign_out": int(payload.get("event_default_sign_out_grace_minutes") or DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES),
                },
            )

            return {
                "action": action,
                "school": _fetch_school(conn, int(inserted)),
                "undo": {
                    "steps": [
                        {
                            "sql": "delete from schools where id = :school_id",
                            "params": {"school_id": int(inserted)},
                        }
                    ]
                },
            }

        if action == "update_school":
            _require_school_admin(roles)
            school_id = _require_school_scope(body, payload)
            existing_school = _fetch_school(conn, int(school_id))
            if not existing_school:
                raise HTTPException(status_code=404, detail="school not found")

            updated_fields: dict[str, Any] = {}
            if "school_name" in payload:
                school_name = _normalize_optional_text(payload.get("school_name"))
                if not school_name:
                    raise HTTPException(status_code=400, detail="payload.school_name cannot be empty")
                updated_fields["name"] = school_name
                updated_fields["school_name"] = school_name
            if "school_code" in payload:
                updated_fields["school_code"] = _normalize_optional_text(payload.get("school_code"))
            if "address" in payload:
                address = _normalize_optional_text(payload.get("address"))
                if not address:
                    raise HTTPException(status_code=400, detail="payload.address cannot be empty")
                updated_fields["address"] = address
            if "logo_url" in payload:
                updated_fields["logo_url"] = _normalize_optional_text(payload.get("logo_url"))
            if "primary_color" in payload:
                updated_fields["primary_color"] = _normalize_optional_text(payload.get("primary_color"))
            if "secondary_color" in payload:
                updated_fields["secondary_color"] = _normalize_optional_text(payload.get("secondary_color"))
            if "subscription_status" in payload and _is_admin(roles):
                updated_fields["subscription_status"] = _normalize_optional_text(payload.get("subscription_status"))
            if "subscription_plan" in payload and _is_admin(roles):
                updated_fields["subscription_plan"] = _normalize_optional_text(payload.get("subscription_plan"))
            if "active_status" in payload and _is_admin(roles):
                updated_fields["active_status"] = _coerce_bool(payload.get("active_status"))
            if "subscription_start" in payload and _is_admin(roles):
                updated_fields["subscription_start"] = _coerce_date(payload.get("subscription_start"))
            if "subscription_end" in payload and _is_admin(roles):
                updated_fields["subscription_end"] = _coerce_date(payload.get("subscription_end"))

            if updated_fields:
                set_sql = ", ".join(f"{column} = :{column}" for column in updated_fields)
                updated_fields["school_id"] = int(school_id)
                conn.execute(
                    text(f"update schools set {set_sql} where id = :school_id"),
                    updated_fields,
                )

            event_fields = {}
            if "event_default_early_check_in_minutes" in payload:
                event_fields["event_default_early_check_in_minutes"] = int(payload["event_default_early_check_in_minutes"])
            if "event_default_late_threshold_minutes" in payload:
                event_fields["event_default_late_threshold_minutes"] = int(payload["event_default_late_threshold_minutes"])
            if "event_default_sign_out_grace_minutes" in payload:
                event_fields["event_default_sign_out_grace_minutes"] = int(payload["event_default_sign_out_grace_minutes"])

            if event_fields:
                settings_exists = existing_school.get("event_default_early_check_in_minutes") is not None
                if settings_exists:
                    set_sql = ", ".join(f"{column} = :{column}" for column in event_fields)
                    event_fields["school_id"] = int(school_id)
                    conn.execute(
                        text(f"update school_settings set {set_sql} where school_id = :school_id"),
                        event_fields,
                    )
                else:
                    conn.execute(
                        text(
                            """
                            insert into school_settings (
                                school_id,
                                primary_color,
                                secondary_color,
                                accent_color,
                                event_default_early_check_in_minutes,
                                event_default_late_threshold_minutes,
                                event_default_sign_out_grace_minutes
                            )
                            values (
                                :school_id,
                                :primary_color,
                                :secondary_color,
                                :accent_color,
                                :early,
                                :late,
                                :sign_out
                            )
                            """
                        ),
                        {
                            "school_id": int(school_id),
                            "primary_color": updated_fields.get("primary_color") or existing_school.get("primary_color") or DEFAULT_PRIMARY_COLOR,
                            "secondary_color": updated_fields.get("secondary_color") or existing_school.get("secondary_color") or DEFAULT_SECONDARY_COLOR,
                            "accent_color": updated_fields.get("secondary_color") or existing_school.get("secondary_color") or DEFAULT_ACCENT_COLOR,
                            "early": event_fields.get("event_default_early_check_in_minutes", DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES),
                            "late": event_fields.get("event_default_late_threshold_minutes", DEFAULT_EVENT_LATE_THRESHOLD_MINUTES),
                            "sign_out": event_fields.get("event_default_sign_out_grace_minutes", DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES),
                        },
                    )

            undo_steps = []
            if updated_fields:
                undo_steps.append(
                    {
                        "sql": """
                            update schools
                            set name = :name,
                                school_name = :school_name,
                                school_code = :school_code,
                                address = :address,
                                logo_url = :logo_url,
                                primary_color = :primary_color,
                                secondary_color = :secondary_color,
                                subscription_status = :subscription_status,
                                active_status = :active_status,
                                subscription_plan = :subscription_plan,
                                subscription_start = :subscription_start,
                                subscription_end = :subscription_end
                            where id = :school_id
                        """,
                        "params": {
                            "school_id": int(school_id),
                            "name": existing_school["name"],
                            "school_name": existing_school["school_name"],
                            "school_code": existing_school["school_code"],
                            "address": existing_school["address"],
                            "logo_url": existing_school["logo_url"],
                            "primary_color": existing_school["primary_color"],
                            "secondary_color": existing_school["secondary_color"],
                            "subscription_status": existing_school["subscription_status"],
                            "active_status": existing_school["active_status"],
                            "subscription_plan": existing_school["subscription_plan"],
                            "subscription_start": existing_school["subscription_start"],
                            "subscription_end": existing_school["subscription_end"],
                        },
                    }
                )
            if event_fields:
                if existing_school.get("event_default_early_check_in_minutes") is not None:
                    undo_steps.append(
                        {
                            "sql": """
                                update school_settings
                                set event_default_early_check_in_minutes = :early,
                                    event_default_late_threshold_minutes = :late,
                                    event_default_sign_out_grace_minutes = :sign_out
                                where school_id = :school_id
                            """,
                            "params": {
                                "school_id": int(school_id),
                                "early": existing_school["event_default_early_check_in_minutes"],
                                "late": existing_school["event_default_late_threshold_minutes"],
                                "sign_out": existing_school["event_default_sign_out_grace_minutes"],
                            },
                        }
                    )
                else:
                    undo_steps.append(
                        {
                            "sql": "delete from school_settings where school_id = :school_id",
                            "params": {"school_id": int(school_id)},
                        }
                    )

            return {
                "action": action,
                "school": _fetch_school(conn, int(school_id)),
                "undo": {"steps": undo_steps},
            }

        if action == "update_school_status":
            _require_admin(roles)
            school_id = _require_school_scope(body, payload)
            existing_school = _fetch_school(conn, int(school_id))
            if not existing_school:
                raise HTTPException(status_code=404, detail="school not found")

            if "active_status" not in payload and "subscription_status" not in payload:
                raise HTTPException(status_code=400, detail="payload.active_status or payload.subscription_status is required")

            active_status = (
                _coerce_bool(payload.get("active_status"))
                if "active_status" in payload
                else existing_school["active_status"]
            )
            subscription_status = (
                _normalize_optional_text(payload.get("subscription_status"))
                if "subscription_status" in payload
                else existing_school["subscription_status"]
            )

            conn.execute(
                text(
                    """
                    update schools
                    set active_status = :active_status,
                        subscription_status = :subscription_status
                    where id = :school_id
                    """
                ),
                {
                    "school_id": int(school_id),
                    "active_status": active_status,
                    "subscription_status": subscription_status,
                },
            )

            return {
                "action": action,
                "school": _fetch_school(conn, int(school_id)),
                "undo": {
                    "steps": [
                        {
                            "sql": """
                                update schools
                                set active_status = :active_status,
                                    subscription_status = :subscription_status
                                where id = :school_id
                            """,
                            "params": {
                                "school_id": int(school_id),
                                "active_status": existing_school["active_status"],
                                "subscription_status": existing_school["subscription_status"],
                            },
                        }
                    ]
                },
            }

        if action == "list_events":
            _require_table_read(policy, "events")
            school_id = _require_school_scope(body, payload, allow_admin_none=True)
            status_value = _normalize_optional_text(payload.get("status"))
            upcoming_only = bool(payload.get("upcoming_only", False))
            limit = int(payload.get("limit") or 20)
            rows = _event_rows(
                conn,
                school_id=school_id,
                status=status_value,
                upcoming_only=upcoming_only,
                limit=limit,
            )
            return {"action": action, "count": len(rows), "rows": rows}

        if action == "list_departments":
            _require_table_read(policy, "departments")
            school_id = _require_school_scope(body, payload, allow_admin_none=True)
            if school_id is None:
                rows = conn.execute(
                    text(
                        """
                        select id, school_id, name
                        from departments
                        order by school_id nulls first, name asc
                        """
                    )
                ).mappings().all()
            else:
                rows = conn.execute(
                    text(
                        """
                        select id, school_id, name
                        from departments
                        where school_id = :school_id
                        order by name asc
                        """
                    ),
                    {"school_id": int(school_id)},
                ).mappings().all()
            return {"action": action, "count": len(rows), "rows": [dict(row) for row in rows]}

        if action == "create_department":
            _require_school_admin(roles)
            _require_table_write(policy, "departments")
            school_id = _require_school_scope(body, payload)
            name = _normalize_optional_text(payload.get("name"))
            if not name:
                raise HTTPException(status_code=400, detail="payload.name is required")

            department_id = conn.execute(
                text(
                    """
                    insert into departments (school_id, name)
                    values (:school_id, :name)
                    returning id
                    """
                ),
                {"school_id": int(school_id), "name": name},
            ).scalar_one()

            return {
                "action": action,
                "department": _fetch_department(conn, int(department_id)),
                "undo": {
                    "steps": [
                        {
                            "sql": "delete from departments where id = :department_id",
                            "params": {"department_id": int(department_id)},
                        }
                    ]
                },
            }

        if action == "update_department":
            _require_school_admin(roles)
            _require_table_write(policy, "departments")
            department_id = payload.get("department_id")
            if department_id is None:
                raise HTTPException(status_code=400, detail="payload.department_id is required")
            existing_department = _fetch_department(conn, int(department_id))
            if not existing_department:
                raise HTTPException(status_code=404, detail="department not found")

            school_id = _require_school_scope(body, {"school_id": existing_department["school_id"]})
            if int(existing_department["school_id"]) != int(school_id):
                raise HTTPException(status_code=403, detail="department scope mismatch")

            name = _normalize_optional_text(payload.get("name"))
            if not name:
                raise HTTPException(status_code=400, detail="payload.name is required")

            conn.execute(
                text("update departments set name = :name where id = :department_id"),
                {"department_id": int(department_id), "name": name},
            )

            return {
                "action": action,
                "department": _fetch_department(conn, int(department_id)),
                "undo": {
                    "steps": [
                        {
                            "sql": "update departments set name = :name where id = :department_id",
                            "params": {
                                "department_id": int(department_id),
                                "name": existing_department["name"],
                            },
                        }
                    ]
                },
            }

        if action == "list_programs":
            _require_table_read(policy, "programs")
            school_id = _require_school_scope(body, payload, allow_admin_none=True)
            rows = _program_rows(conn, school_id)
            return {"action": action, "count": len(rows), "rows": rows}

        if action == "create_program":
            _require_school_admin(roles)
            _require_table_write(policy, "programs")
            school_id = _require_school_scope(body, payload)
            name = _normalize_optional_text(payload.get("name"))
            if not name:
                raise HTTPException(status_code=400, detail="payload.name is required")

            department_ids = [int(value) for value in (payload.get("department_ids") or [])]
            _validate_department_ids(conn, int(school_id), department_ids)

            program_id = conn.execute(
                text(
                    """
                    insert into programs (school_id, name)
                    values (:school_id, :name)
                    returning id
                    """
                ),
                {"school_id": int(school_id), "name": name},
            ).scalar_one()

            for department_id in department_ids:
                conn.execute(
                    text(
                        """
                        insert into program_department_association (program_id, department_id)
                        values (:program_id, :department_id)
                        """
                    ),
                    {"program_id": int(program_id), "department_id": int(department_id)},
                )

            return {
                "action": action,
                "program": _fetch_program(conn, int(program_id)),
                "undo": {
                    "steps": [
                        {
                            "sql": "delete from programs where id = :program_id",
                            "params": {"program_id": int(program_id)},
                        }
                    ]
                },
            }

        if action == "update_program":
            _require_school_admin(roles)
            _require_table_write(policy, "programs")
            program_id = payload.get("program_id")
            if program_id is None:
                raise HTTPException(status_code=400, detail="payload.program_id is required")
            existing_program = _fetch_program(conn, int(program_id))
            if not existing_program:
                raise HTTPException(status_code=404, detail="program not found")

            school_id = _require_school_scope(body, {"school_id": existing_program["school_id"]})
            if int(existing_program["school_id"]) != int(school_id):
                raise HTTPException(status_code=403, detail="program scope mismatch")

            undo_steps: list[dict[str, Any]] = []

            if "name" in payload:
                name = _normalize_optional_text(payload.get("name"))
                if not name:
                    raise HTTPException(status_code=400, detail="payload.name cannot be empty")
                conn.execute(
                    text("update programs set name = :name where id = :program_id"),
                    {"program_id": int(program_id), "name": name},
                )
                undo_steps.append(
                    {
                        "sql": "update programs set name = :name where id = :program_id",
                        "params": {
                            "program_id": int(program_id),
                            "name": existing_program["name"],
                        },
                    }
                )

            if "department_ids" in payload:
                department_ids = [int(value) for value in (payload.get("department_ids") or [])]
                _validate_department_ids(conn, int(school_id), department_ids)
                conn.execute(
                    text("delete from program_department_association where program_id = :program_id"),
                    {"program_id": int(program_id)},
                )
                for department_id in department_ids:
                    conn.execute(
                        text(
                            """
                            insert into program_department_association (program_id, department_id)
                            values (:program_id, :department_id)
                            """
                        ),
                        {"program_id": int(program_id), "department_id": int(department_id)},
                    )

                old_department_ids = list(existing_program.get("department_ids") or [])
                undo_steps.append(
                    {
                        "sql": "delete from program_department_association where program_id = :program_id",
                        "params": {"program_id": int(program_id)},
                    }
                )
                for department_id in old_department_ids:
                    undo_steps.append(
                        {
                            "sql": """
                                insert into program_department_association (program_id, department_id)
                                values (:program_id, :department_id)
                            """,
                            "params": {
                                "program_id": int(program_id),
                                "department_id": int(department_id),
                            },
                        }
                    )

            return {
                "action": action,
                "program": _fetch_program(conn, int(program_id)),
                "undo": {"steps": undo_steps},
            }

    raise HTTPException(status_code=400, detail=f"unsupported school admin action: {body.action}")


@app.post("/action")
def run_action(body: ActionRequest) -> dict[str, Any]:
    try:
        return _run_action_internal(body)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=400, detail=f"school admin action failed: {exc}") from exc

"""Role-scoped query service.

POST /query
Structured (preferred):
{
  "role": "student",
  "table": "events",
  "columns": ["id", "title"],
  "filters": {"school_id": 1},
  "limit": 50
}

Raw SQL (strictly validated):
{
  "role": "campus_admin",
  "sql": "select id, title from events where school_id = :school_id limit 50",
  "params": {"school_id": 1}
}
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from policy import (
    AccessPolicy,
    filter_allowed_columns,
    get_effective_policy,
    normalize_permission,
    normalize_role,
)


TENANT_DATABASE_URL = (
    os.getenv("TENANT_DATABASE_URL")
    or os.getenv("APP_DATABASE_URL")
    or os.getenv("DATABASE_URL")
)

if not TENANT_DATABASE_URL:
    raise RuntimeError("TENANT_DATABASE_URL (or APP_DATABASE_URL/DATABASE_URL) is required.")

engine = create_engine(TENANT_DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="MCP Query Service")


class QueryRequest(BaseModel):
    role: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    user_id: Optional[str] = None
    school_id: Optional[int] = None
    sql: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    table: Optional[str] = None
    columns: Optional[list[str]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = 100
    count_only: bool = False


DISALLOWED_SQL = re.compile(
    r"\b(delete|drop|alter|create|grant|revoke|truncate)\b",
    re.IGNORECASE,
)

SENSITIVE_COLUMN_NAMES = {
    "password_hash",
    "face_encoding",
    "rfid_tag",
}

SENSITIVE_WILDCARD_TABLES = {
    "users",
    "student_profiles",
}

MCP_READ_ONLY_TABLES = {
    "event_sanction_configs",
    "sanction_records",
    "sanction_items",
    "sanction_delegations",
    "sanction_compliance_history",
    "clearance_deadlines",
}


def _resolve_roles(body: QueryRequest) -> list[str]:
    combined = [*body.roles]
    if body.role:
        combined.append(body.role)

    normalized_roles: list[str] = []
    seen = set()
    for role in combined:
        normalized_role = normalize_role(role)
        if not normalized_role or normalized_role in seen:
            continue
        seen.add(normalized_role)
        normalized_roles.append(normalized_role)
    return normalized_roles


def _resolve_permissions(body: QueryRequest) -> list[str]:
    normalized_permissions: list[str] = []
    seen = set()
    for permission in body.permissions:
        normalized_permission = normalize_permission(permission)
        if not normalized_permission or normalized_permission in seen:
            continue
        seen.add(normalized_permission)
        normalized_permissions.append(normalized_permission)
    return normalized_permissions


def _resolve_policy(body: QueryRequest) -> tuple[list[str], list[str], AccessPolicy]:
    roles = _resolve_roles(body)
    if not roles:
        raise HTTPException(status_code=400, detail="role or roles are required")
    permissions = _resolve_permissions(body)
    return roles, permissions, get_effective_policy(roles, permissions)


def _get_expected_scope_value(body: QueryRequest, filter_name: str) -> Any:
    if filter_name == "school_id":
        return body.school_id
    if filter_name == "user_id":
        return body.user_id
    return None


def _extract_table_names(sql: str) -> set[str]:
    table_names = re.findall(
        r"\bfrom\s+([a-zA-Z0-9_]+)|\bjoin\s+([a-zA-Z0-9_]+)|\bupdate\s+([a-zA-Z0-9_]+)|\binsert\s+into\s+([a-zA-Z0-9_]+)",
        sql,
        re.IGNORECASE,
    )
    return {t for quad in table_names for t in quad if t}


def _require_filters(
    policy: AccessPolicy,
    body: QueryRequest,
    table: Optional[str],
    filters: dict[str, Any],
    sql: Optional[str],
) -> None:
    if sql is not None:
        for sql_table in _extract_table_names(sql):
            for required in policy.required_filters.get(sql_table, set()):
                if required not in sql:
                    raise HTTPException(
                        status_code=400,
                        detail=f"missing required filter in SQL for {sql_table}: {required}",
                    )
                expected_value = _get_expected_scope_value(body, required)
                if expected_value is not None:
                    if f":{required}" not in sql:
                        raise HTTPException(
                            status_code=400,
                            detail=f"required filter for {sql_table} must be parameterized as :{required}",
                        )
                    if str(body.params.get(required)) != str(expected_value):
                        raise HTTPException(
                            status_code=400,
                            detail=f"scope param mismatch for {sql_table}: {required}",
                        )
        return

    if not table:
        return

    for required in policy.required_filters.get(table, set()):
        if required not in filters:
            raise HTTPException(
                status_code=400,
                detail=f"missing required filter for {table}: {required}",
            )
        expected_value = _get_expected_scope_value(body, required)
        if expected_value is not None and str(filters.get(required)) != str(expected_value):
            raise HTTPException(
                status_code=400,
                detail=f"scope filter mismatch for {table}: {required}",
            )


def _validate_sql(policy: AccessPolicy, sql: str) -> None:
    if DISALLOWED_SQL.search(sql or ""):
        raise HTTPException(status_code=400, detail="DELETE/DDL statements are not allowed")
    if ";" in sql.strip().rstrip(";"):
        raise HTTPException(status_code=400, detail="multiple statements are not allowed")

    found_tables = _extract_table_names(sql)
    if not found_tables:
        raise HTTPException(status_code=400, detail="could not detect table name in SQL")
    for table in found_tables:
        if table not in policy.allowed_tables:
            raise HTTPException(status_code=403, detail=f"table not allowed: {table}")

    for column_name in SENSITIVE_COLUMN_NAMES:
        if re.search(rf"\b{re.escape(column_name)}\b", sql, re.IGNORECASE):
            raise HTTPException(status_code=403, detail=f"sensitive column access denied: {column_name}")

    for table in found_tables:
        if table not in SENSITIVE_WILDCARD_TABLES:
            continue
        if re.search(rf"\bselect\s+\*\s+from\s+{re.escape(table)}\b", sql, re.IGNORECASE):
            raise HTTPException(status_code=403, detail=f"wildcard select is not allowed for sensitive table: {table}")
        if re.search(rf"\bselect\s+{re.escape(table)}\.\*\b", sql, re.IGNORECASE):
            raise HTTPException(status_code=403, detail=f"wildcard select is not allowed for sensitive table: {table}")


def _is_write(sql: str) -> bool:
    return bool(re.search(r"^\s*(insert|update)\b", sql, re.IGNORECASE))


def _extract_table_from_update(sql: str) -> Optional[str]:
    m = re.search(r"\bupdate\s+([a-zA-Z0-9_]+)\b", sql, re.IGNORECASE)
    return m.group(1) if m else None


def _extract_table_from_insert(sql: str) -> Optional[str]:
    m = re.search(r"\binsert\s+into\s+([a-zA-Z0-9_]+)\b", sql, re.IGNORECASE)
    return m.group(1) if m else None


def _extract_where_clause(sql: str) -> Optional[str]:
    m = re.search(r"\bwhere\b(.+)", sql, re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    clause = m.group(1)
    # Strip trailing ORDER BY / LIMIT if present
    clause = re.split(r"\border\s+by\b|\blimit\b", clause, flags=re.IGNORECASE)[0]
    return clause.strip()


def _get_primary_keys(conn, table: str) -> list[str]:
    rows = conn.execute(
        text(
            """
            select kcu.column_name
            from information_schema.table_constraints tc
            join information_schema.key_column_usage kcu
              on tc.constraint_name = kcu.constraint_name
             and tc.table_schema = kcu.table_schema
            where tc.constraint_type = 'PRIMARY KEY'
              and tc.table_name = :table
              and tc.table_schema = 'public'
            order by kcu.ordinal_position
            """
        ),
        {"table": table},
    ).fetchall()
    return [r[0] for r in rows]


@app.post("/query")
def run_query(body: QueryRequest) -> Dict[str, Any]:
    _roles, _permissions, policy = _resolve_policy(body)

    if body.sql:
        _validate_sql(policy, body.sql)
        _require_filters(policy, body, None, {}, body.sql)
        query = text(body.sql)
        params = body.params or {}
    else:
        if not body.table:
            raise HTTPException(status_code=400, detail="table is required when sql is not provided")

        if body.table not in policy.allowed_tables:
            raise HTTPException(status_code=403, detail=f"table not allowed: {body.table}")

        columns = body.columns or ["*"]
        allowed_columns = policy.allowed_columns.get(body.table)
        if columns == ["*"] and allowed_columns:
            columns = sorted(allowed_columns)
        elif columns != ["*"]:
            columns = filter_allowed_columns(policy, body.table, columns)
        _require_filters(policy, body, body.table, body.filters, None)

        where_parts = []
        params = {}
        for key, value in (body.filters or {}).items():
            param_key = f"f_{key}"
            where_parts.append(f"{key} = :{param_key}")
            params[param_key] = value

        where_sql = f" where {' and '.join(where_parts)}" if where_parts else ""
        limit = max(1, min(body.limit, 500))
        if body.count_only:
            query = text(f"select count(*) as count from {body.table}{where_sql}")
        else:
            query = text(f"select {', '.join(columns)} from {body.table}{where_sql} limit {limit}")

    try:
        with engine.begin() as conn:
            if body.sql and _is_write(body.sql):
                if body.sql.strip().lower().startswith("insert"):
                    table = _extract_table_from_insert(body.sql)
                else:
                    table = _extract_table_from_update(body.sql)
                if not table:
                    raise HTTPException(status_code=400, detail="could not detect table for write query")
                if table in MCP_READ_ONLY_TABLES:
                    raise HTTPException(
                        status_code=403,
                        detail=f"write is not allowed through MCP for table: {table}",
                    )
                if table not in policy.allowed_write_tables:
                    raise HTTPException(status_code=403, detail=f"write not allowed for table: {table}")

                if body.sql.strip().lower().startswith("update"):
                    where_clause = _extract_where_clause(body.sql)
                    if not where_clause:
                        raise HTTPException(status_code=400, detail="UPDATE requires a WHERE clause")

                    # Capture pre-update rows for undo.
                    pre_rows = conn.execute(
                        text(f"select * from {table} where {where_clause}"),
                        params,
                    ).fetchall()

                    result = conn.execute(query, params)
                    updated_count = result.rowcount or 0

                    pk_cols = _get_primary_keys(conn, table)
                    undo_steps = []
                    for row in pre_rows:
                        row_map = dict(row._mapping)
                        if not pk_cols:
                            continue
                        pk_filter = " and ".join([f"{k} = :pk_{k}" for k in pk_cols])
                        set_parts = [f"{k} = :old_{k}" for k in row_map.keys()]
                        undo_sql = f"update {table} set {', '.join(set_parts)} where {pk_filter}"
                        undo_params = {f"old_{k}": v for k, v in row_map.items()}
                        undo_params.update({f"pk_{k}": row_map[k] for k in pk_cols})
                        undo_steps.append({"sql": undo_sql, "params": undo_params})

                    return {
                        "count": updated_count,
                        "rows": [],
                        "undo": {
                            "steps": undo_steps,
                            "note": "Use /undo to roll back. Delete is disallowed in normal queries.",
                        },
                    }

                # INSERT: require RETURNING so we can build undo.
                if "returning" not in body.sql.lower():
                    raise HTTPException(
                        status_code=400,
                        detail="INSERT must include RETURNING for undo support",
                    )

                rows = conn.execute(query, params).fetchall()
                pk_cols = _get_primary_keys(conn, table)
                if not pk_cols:
                    raise HTTPException(status_code=400, detail="could not determine primary key for undo")

                pk_filters = []
                undo_params = {}
                for idx, row in enumerate(rows):
                    row_map = dict(row._mapping)
                    parts = []
                    for pk in pk_cols:
                        key = f"pk_{pk}_{idx}"
                        parts.append(f"{pk} = :{key}")
                        undo_params[key] = row_map[pk]
                    pk_filters.append("(" + " and ".join(parts) + ")")
                undo_sql = f"delete from {table} where " + " or ".join(pk_filters)

                return {
                    "count": len(rows),
                    "rows": [dict(r._mapping) for r in rows],
                    "undo": {
                        "steps": [{"sql": undo_sql, "params": undo_params}],
                        "note": "Use /undo to roll back. Delete is disallowed in normal queries.",
                    },
                }

            rows = conn.execute(query, params).fetchall()
            if body.count_only:
                count_value = 0
                if rows:
                    count_value = int(rows[0]._mapping.get("count", 0) or 0)
                return {
                    "count": count_value,
                    "rows": [dict(row._mapping) for row in rows],
                    "mode": "count",
                }
            return {
                "count": len(rows),
                "rows": [dict(row._mapping) for row in rows],
            }
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=400, detail=f"database query failed: {exc}") from exc


@app.post("/undo")
def run_undo(payload: Dict[str, Any]) -> Dict[str, Any]:
    steps = payload.get("steps") or []
    if not steps:
        raise HTTPException(status_code=400, detail="undo steps required")

    try:
        with engine.begin() as conn:
            applied = 0
            for step in steps:
                if not isinstance(step, dict):
                    raise HTTPException(status_code=400, detail="invalid undo step payload")

                sql = step.get("sql") or ""
                params = step.get("params") or {}
                # Undo may need INSERT when restoring association rows.
                if not re.match(r"^\s*(insert|update|delete)\b", sql, re.IGNORECASE):
                    raise HTTPException(status_code=400, detail="invalid undo step")
                conn.execute(text(sql), params)
                applied += 1
        return {"applied": applied}
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=400, detail=f"undo failed: {exc}") from exc

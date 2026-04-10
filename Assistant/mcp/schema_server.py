"""Role-scoped schema service.

POST /schema
{
  "role": "student"
}
"""

from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

from policy import (
    filter_allowed_tables,
    get_effective_policy,
    normalize_permission,
    normalize_role,
    summarize_scope_rules,
)


TENANT_DATABASE_URL = (
    os.getenv("TENANT_DATABASE_URL")
    or os.getenv("APP_DATABASE_URL")
    or os.getenv("DATABASE_URL")
)

if not TENANT_DATABASE_URL:
    raise RuntimeError("TENANT_DATABASE_URL (or APP_DATABASE_URL/DATABASE_URL) is required.")

engine = create_engine(TENANT_DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="MCP Schema Service")


class SchemaRequest(BaseModel):
    role: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    db_schema: str | None = "public"


def _resolve_roles(body: SchemaRequest) -> list[str]:
    combined = [*body.roles]
    if body.role:
        combined.append(body.role)
    normalized = []
    seen = set()
    for role in combined:
        normalized_role = normalize_role(role)
        if not normalized_role or normalized_role in seen:
            continue
        seen.add(normalized_role)
        normalized.append(normalized_role)
    return normalized


def _resolve_permissions(body: SchemaRequest) -> list[str]:
    normalized = []
    seen = set()
    for permission in body.permissions:
        normalized_permission = normalize_permission(permission)
        if not normalized_permission or normalized_permission in seen:
            continue
        seen.add(normalized_permission)
        normalized.append(normalized_permission)
    return normalized


def _serialize_column_type(column_type: Any) -> str:
    if column_type is None:
        return "unknown"
    return str(column_type)


@app.post("/schema")
def get_schema(body: SchemaRequest) -> Dict[str, Any]:
    roles = _resolve_roles(body)
    if not roles:
        raise HTTPException(status_code=400, detail="role or roles are required")
    permissions = _resolve_permissions(body)

    db_schema = body.db_schema or "public"

    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            table_names = sorted(inspector.get_table_names(schema=db_schema))
            tables: dict[str, list[dict[str, Any]]] = {}

            for table_name in table_names:
                columns = inspector.get_columns(table_name, schema=db_schema)
                serialized_columns: list[dict[str, Any]] = []

                for column in columns:
                    column_type = column.get("type")
                    column_meta: dict[str, Any] = {
                        "name": column["name"],
                        "type": _serialize_column_type(column_type),
                    }
                    enum_values = list(getattr(column_type, "enums", []) or [])
                    if enum_values:
                        column_meta["enum_values"] = enum_values
                    serialized_columns.append(column_meta)

                tables[table_name] = serialized_columns
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=400, detail=f"schema lookup failed: {exc}") from exc

    policy = get_effective_policy(roles, permissions)
    allowed_tables = set(filter_allowed_tables(policy, tables.keys()))

    filtered: dict[str, list[dict[str, Any]]] = {}
    for table_name, columns in tables.items():
        if table_name not in allowed_tables:
            continue
        allowed_cols = policy.allowed_columns.get(table_name)
        if allowed_cols:
            filtered[table_name] = [c for c in columns if c["name"] in allowed_cols]
        else:
            filtered[table_name] = columns

    return {
        "schema": db_schema,
        "roles": roles,
        "permissions": permissions,
        "readable_tables": sorted(policy.allowed_tables),
        "writable_tables": sorted(policy.allowed_write_tables),
        "scope_rules": summarize_scope_rules(policy),
        "tables": filtered,
    }

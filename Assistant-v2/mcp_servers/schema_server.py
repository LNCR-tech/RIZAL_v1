import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

# Ensure lib/ is in the path for imports
LIB_DIR = str(Path(__file__).resolve().parent.parent / "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from database import app_engine
from policy import (
    filter_allowed_tables,
    get_effective_policy,
    normalize_permission,
    normalize_role,
    summarize_scope_rules
)

# Initialize FastMCP Server
mcp = FastMCP("Aura Schema Server")

def _serialize_column_type(column_type: Any) -> str:
    if column_type is None:
        return "unknown"
    return str(column_type)

@mcp.tool()
async def mcp_schema(
    roles: List[str], 
    permissions: Optional[List[str]] = None,
    db_schema: str = "public"
) -> Dict[str, Any]:
    """
    Returns the database schema (tables and columns) that the user is allowed to see 
    based on their roles and permissions. This is capability-scoped.
    """
    if not app_engine:
        return {"error": "Application database is not configured."}

    # Normalize inputs
    norm_roles = [normalize_role(r) for r in roles if normalize_role(r)]
    norm_perms = [normalize_permission(p) for p in (permissions or []) if normalize_permission(p)]

    if not norm_roles:
        return {"error": "At least one valid role is required."}

    try:
        with app_engine.connect() as conn:
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
        return {"error": f"Schema lookup failed: {str(exc)}"}

    # Apply Policy Filtering
    policy = get_effective_policy(norm_roles, norm_perms)
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
        "db_schema": db_schema,
        "roles": norm_roles,
        "permissions": norm_perms,
        "readable_tables": sorted(list(policy.allowed_tables)),
        "scope_rules": summarize_scope_rules(policy),
        "tables": filtered,
    }

if __name__ == "__main__":
    mcp.run()

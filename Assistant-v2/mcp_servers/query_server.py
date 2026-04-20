import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Ensure lib/ is in the path for imports
LIB_DIR = str(Path(__file__).resolve().parent.parent / "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from database import app_engine
from policy import (
    AccessPolicy,
    filter_allowed_columns,
    get_effective_policy,
    normalize_permission,
    normalize_role
)

# Initialize FastMCP Server
mcp = FastMCP("Aura Query Server")

# --- Safety Constants ---
DISALLOWED_SQL = re.compile(
    r"\b(delete|drop|alter|create|grant|revoke|truncate)\b",
    re.IGNORECASE,
)

SENSITIVE_COLUMN_NAMES = {"password_hash", "face_encoding", "rfid_tag"}
SENSITIVE_WILDCARD_TABLES = {"users", "student_profiles"}
MCP_READ_ONLY_TABLES = {
    "event_sanction_configs", "sanction_records", "sanction_items",
    "sanction_delegations", "sanction_compliance_history", "clearance_deadlines"
}

# --- Helper Functions ---
def _extract_table_names(sql: str) -> set[str]:
    table_names = re.findall(
        r"\bfrom\s+([a-zA-Z0-9_]+)|\bjoin\s+([a-zA-Z0-9_]+)|\bupdate\s+([a-zA-Z0-9_]+)|\binsert\s+into\s+([a-zA-Z0-9_]+)",
        sql, re.IGNORECASE
    )
    return {t for quad in table_names for t in quad if t}

def _validate_sql(policy: AccessPolicy, sql: str) -> None:
    if DISALLOWED_SQL.search(sql or ""):
        raise ValueError("DELETE/DDL statements are not allowed")
    if ";" in sql.strip().rstrip(";"):
        raise ValueError("multiple statements are not allowed")

    found_tables = _extract_table_names(sql)
    if not found_tables:
        raise ValueError("could not detect table name in SQL")
    for table in found_tables:
        if table not in policy.allowed_tables:
            raise ValueError(f"table not allowed: {table}")

    for column_name in SENSITIVE_COLUMN_NAMES:
        if re.search(rf"\b{re.escape(column_name)}\b", sql, re.IGNORECASE):
            raise ValueError(f"sensitive column access denied: {column_name}")

def _is_write(sql: str) -> bool:
    return bool(re.search(r"^\s*(insert|update)\b", sql, re.IGNORECASE))

@mcp.tool()
async def execute_query(
    roles: List[str],
    user_id: str,
    school_id: int,
    permissions: Optional[List[str]] = None,
    sql: Optional[str] = None,
    params: Dict[str, Any] = None,
    table: Optional[str] = None,
    columns: Optional[List[str]] = None,
    filters: Dict[str, Any] = None,
    limit: int = 100,
    count_only: bool = False
) -> Dict[str, Any]:
    """
    Executes a database query. Supports both raw SQL (validated) and structured queries.
    Enforces security policies based on the provided roles and identifiers.
    """
    if not app_engine:
        return {"error": "Application database is not configured."}

    # Normalize roles/perms
    norm_roles = [normalize_role(r) for r in roles if normalize_role(r)]
    norm_perms = [normalize_permission(p) for p in (permissions or []) if normalize_permission(p)]
    policy = get_effective_policy(norm_roles, norm_perms)

    if sql:
        try:
            _validate_sql(policy, sql)
            # Basic scope check check in SQL string
            if "school_id" in policy.required_filters.get(_extract_table_names(sql).pop() if _extract_table_names(sql) else "", {}):
                 if "school_id" not in sql:
                     return {"error": "missing required school_id filter in SQL"}
            
            query_text = text(sql)
            query_params = params or {}
        except Exception as e:
            return {"error": str(e)}
    else:
        if not table:
            return {"error": "table is required when sql is not provided"}
        if table not in policy.allowed_tables:
            return {"error": f"table not allowed: {table}"}

        cols = columns or ["*"]
        allowed_cols = policy.allowed_columns.get(table)
        if cols == ["*"] and allowed_cols:
            cols = sorted(allowed_cols)
        elif cols != ["*"]:
            cols = filter_allowed_columns(policy, table, cols)
        
        where_parts = []
        query_params = {}
        
        # Enforce required filters
        required = policy.required_filters.get(table, set())
        for r in required:
            val = school_id if r == "school_id" else (user_id if r == "user_id" else None)
            if val is not None:
                where_parts.append(f"{r} = :{r}")
                query_params[r] = val

        # Add additional filters
        for k, v in (filters or {}).items():
            if k not in query_params:
                where_parts.append(f"{k} = :f_{k}")
                query_params[f"f_{k}"] = v

        where_sql = f" where {' and '.join(where_parts)}" if where_parts else ""
        safe_limit = max(1, min(limit, 500))
        
        if count_only:
            query_text = text(f"select count(*) as count from {table}{where_sql}")
        else:
            query_text = text(f"select {', '.join(cols)} from {table}{where_sql} limit {safe_limit}")

    try:
        with app_engine.connect() as conn:
            result = conn.execute(query_text, query_params)
            if _is_write(sql or ""):
                # v2 focuses on safe reads for now, but keeping write detection
                return {"error": "Writes are currently being migrated to a separate management tool."}
            
            rows = result.mappings().all()
            return {
                "count": len(rows),
                "rows": [dict(r) for r in rows]
            }
    except SQLAlchemyError as exc:
        return {"error": f"Database query failed: {str(exc)}"}

if __name__ == "__main__":
    mcp.run()

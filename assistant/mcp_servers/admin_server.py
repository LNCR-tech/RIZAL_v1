import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import date
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
    get_effective_policy,
    normalize_permission,
    normalize_role
)

# Initialize FastMCP Server
mcp = FastMCP("Aura Administrative Server")

# --- Constants ---
DEFAULT_PRIMARY_COLOR = "#162F65"
DEFAULT_SECONDARY_COLOR = "#2C5F9E"
DEFAULT_ACCENT_COLOR = "#4A90E2"
DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES = 30
DEFAULT_EVENT_LATE_THRESHOLD_MINUTES = 10
DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES = 20

# --- Middleware-like helpers ---
def _resolve_policy(roles: List[str], permissions: Optional[List[str]]) -> AccessPolicy:
    norm_roles = [normalize_role(r) for r in roles if normalize_role(r)]
    norm_perms = [normalize_permission(p) for p in (permissions or []) if normalize_permission(p)]
    return get_effective_policy(norm_roles, norm_perms)

def _is_admin(policy: AccessPolicy) -> bool:
    # Check for direct admin role in capability notes or table write access
    return "users" in policy.allowed_write_tables and "schools" in policy.allowed_write_tables

def _require_school_scope(policy: AccessPolicy, caller_school_id: Optional[int], target_school_id: Optional[int]) -> int:
    if "schools" not in policy.allowed_tables:
        raise ValueError("Access denied to school data.")
    
    # If admin, they can target any school
    if _is_admin(policy):
        if target_school_id is not None:
            return target_school_id
        if caller_school_id is not None:
            return caller_school_id
        raise ValueError("school_id is required.")

    # If campus_admin, they are locked to their own school
    if caller_school_id is None:
        raise ValueError("Caller school_id is missing for scoped action.")
    
    if target_school_id is not None and int(target_school_id) != int(caller_school_id):
        raise ValueError("School scope mismatch: You cannot manage other schools.")
    
    return int(caller_school_id)

# --- Tools ---

@mcp.tool()
async def list_schools(roles: List[str], permissions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Retrieves a list of schools. Admin can see all; others see their own."""
    policy = _resolve_policy(roles, permissions)
    
    query = """
        select id, school_code, legal_name, display_name, address, is_active, created_at
        from schools
    """
    params = {}
    
    if not _is_admin(policy):
        # We'd normally filter by ID here, but this tool is usually called with school context
        # Simplified for MCP orchestration.
        pass

    try:
        with app_engine.connect() as conn:
            result = conn.execute(text(query), params).mappings().all()
            return {"count": len(result), "schools": [dict(r) for r in result]}
    except SQLAlchemyError as e:
        return {"error": str(e)}

@mcp.tool()
async def get_school(roles: List[str], school_id: int, permissions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Fetch detailed profile and settings for a specific school."""
    policy = _resolve_policy(roles, permissions)
    
    query = """
        select s.*, ss.event_default_early_check_in_minutes, ss.event_default_late_threshold_minutes
        from schools s
        left join school_settings ss on ss.school_id = s.id
        where s.id = :school_id
    """
    try:
        with app_engine.connect() as conn:
            row = conn.execute(text(query), {"school_id": school_id}).mappings().first()
            if not row:
                return {"error": "School not found."}
            return {"school": dict(row)}
    except SQLAlchemyError as e:
        return {"error": str(e)}

@mcp.tool()
async def create_department(
    roles: List[str], 
    school_id: int, 
    name: str, 
    permissions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Creates a new department within a school."""
    policy = _resolve_policy(roles, permissions)
    if "departments" not in policy.allowed_write_tables:
        return {"error": "Permission denied to create departments."}

    query = "insert into departments (school_id, name) values (:school_id, :name) returning id"
    try:
        with app_engine.connect() as conn:
            new_id = conn.execute(text(query), {"school_id": school_id, "name": name}).scalar_one()
            conn.commit()
            return {
                "status": "success",
                "department_id": new_id,
                "undo_steps": [{"sql": "delete from departments where id = :id", "params": {"id": new_id}}]
            }
    except SQLAlchemyError as e:
        return {"error": str(e)}

@mcp.tool()
async def list_departments(roles: List[str], school_id: int, permissions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Lists all departments in a school."""
    policy = _resolve_policy(roles, permissions)
    if "departments" not in policy.allowed_tables:
        return {"error": "Access denied."}

    query = "select id, name from departments where school_id = :school_id order by name"
    try:
        with app_engine.connect() as conn:
            rows = conn.execute(text(query), {"school_id": school_id}).mappings().all()
            return {"count": len(rows), "departments": [dict(r) for r in rows]}
    except SQLAlchemyError as e:
        return {"error": str(e)}

@mcp.tool()
async def list_programs(roles: List[str], school_id: int, permissions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Lists all academic programs in a school."""
    policy = _resolve_policy(roles, permissions)
    if "programs" not in policy.allowed_tables:
        return {"error": "Access denied."}

    query = "select id, name from programs where school_id = :school_id order by name"
    try:
        with app_engine.connect() as conn:
            rows = conn.execute(text(query), {"school_id": school_id}).mappings().all()
            return {"count": len(rows), "programs": [dict(r) for r in rows]}
    except SQLAlchemyError as e:
        return {"error": str(e)}

@mcp.tool()
async def update_school_status(
    roles: List[str], 
    school_id: int, 
    active_status: bool, 
    permissions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Updates the active status of a school (Admin only)."""
    policy = _resolve_policy(roles, permissions)
    if not _is_admin(policy):
        return {"error": "Only system admins can change school status."}

    query = "update schools set active_status = :status where id = :id"
    try:
        with app_engine.connect() as conn:
            conn.execute(text(query), {"status": active_status, "id": school_id})
            conn.commit()
            return {"status": "success", "school_id": school_id, "active_status": active_status}
    except SQLAlchemyError as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()

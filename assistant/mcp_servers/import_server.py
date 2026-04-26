import os
import sys
import csv
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
import httpx
from openpyxl import Workbook

# Ensure lib/ is in the path for imports
LIB_DIR = str(Path(__file__).resolve().parent.parent / "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from app_settings import APP_SETTINGS, get_backend_api_base_url
from policy import normalize_role

# Initialize FastMCP Server
mcp = FastMCP("Aura Import Server")

EXPECTED_HEADERS = [
    "Student_ID", "Email", "Last Name", "First Name", "Middle Name", "Department", "Course"
]

HEADER_ALIASES = {
    "student_id": "Student_ID", "student id": "Student_ID", "id": "Student_ID",
    "email": "Email", "last_name": "Last Name", "last name": "Last Name",
    "first_name": "First Name", "first name": "First Name", "middle_name": "Middle Name",
    "middle name": "Middle Name", "department": "Department", "college": "Department",
    "course": "Course", "program": "Course"
}

# --- Helpers ---
def _normalize_header(header: Any) -> str:
    return re.sub(r"\s+", " ", str(header or "").strip().lower())

def _detect_format(dataset_text: str, dataset_format: str) -> str:
    requested = (dataset_format or "auto").strip().lower()
    if requested in {"csv", "tsv", "json", "markdown"}:
        return requested
    stripped = dataset_text.lstrip()
    if stripped.startswith("[") or stripped.startswith("{"):
        return "json"
    return "csv"

def _parse_dataset(dataset_text: str, dataset_format: str) -> List[Dict[str, str]]:
    # Simple CSV parser for now - in production, use a more robust one from v1
    f = io.StringIO(dataset_text)
    reader = csv.DictReader(f)
    return [row for row in reader]

def _build_workbook_bytes(rows: List[Dict[str, str]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(EXPECTED_HEADERS)
    for row in rows:
        ws.append([row.get(h, "") for h in EXPECTED_HEADERS])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()

# --- Tools ---

@mcp.tool()
async def mcp_import_student(
    roles: List[str],
    action: str,
    authorization: str,
    dataset_text: Optional[str] = None,
    dataset_format: str = "auto",
    preview_token: Optional[str] = None,
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handles bulk student imports (preview, clean, commit, status).
    Requires a valid 'authorization' bearer token.
    """
    norm_roles = [normalize_role(r) for r in roles]
    if not any(r in {"admin", "campus_admin"} for r in norm_roles):
        return {"error": "Permission denied for student imports."}

    backend_api_base_url = get_backend_api_base_url()
    if not backend_api_base_url:
        return {"error": "Backend API not configured."}

    headers = {"Authorization": authorization}
    
    async with httpx.AsyncClient(timeout=APP_SETTINGS.import_request_timeout_seconds) as client:
        if action == "expected_headers":
            return {"expected_headers": EXPECTED_HEADERS, "formats": ["csv", "json"]}

        if action == "preview_import":
            if not dataset_text:
                return {"error": "dataset_text required."}
            rows = _parse_dataset(dataset_text, dataset_format)
            xlsx = _build_workbook_bytes(rows)
            files = {"file": ("import.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            resp = await client.post(f"{backend_api_base_url}/api/admin/import-students/preview", headers=headers, files=files)
            return resp.json()

        if action == "commit_import":
            if not preview_token:
                return {"error": "preview_token required."}
            resp = await client.post(f"{backend_api_base_url}/api/admin/import-students", headers=headers, data={"preview_token": preview_token})
            return resp.json()

        if action == "import_status":
            if not job_id:
                return {"error": "job_id required."}
            resp = await client.get(f"{backend_api_base_url}/api/admin/import-status/{job_id}", headers=headers)
            return resp.json()

    return {"error": f"Unknown action: {action}"}

if __name__ == "__main__":
    mcp.run()

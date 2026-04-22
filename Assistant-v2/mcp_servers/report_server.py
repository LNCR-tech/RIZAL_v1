import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
import httpx

# Ensure lib/ is in the path for imports
LIB_DIR = str(Path(__file__).resolve().parent.parent / "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

# Initialize FastMCP Server
mcp = FastMCP("Aura Reporting Server")

# --- Constants ---
BACKEND_API_BASE_URL = os.getenv("BACKEND_API_BASE_URL")

@mcp.tool()
async def mcp_report(
    action: str,
    authorization: str,
    params: Optional[Dict[str, Any]] = None,
    student_id: Optional[int] = None,
    event_id: Optional[int] = None,
    governance_unit_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fetches pre-calculated reports from the backend (attendance, governance).
    Requires a valid 'authorization' bearer token.
    """
    if not BACKEND_API_BASE_URL:
        return {"error": "Backend API not configured."}

    action_name = action.strip().lower()
    path: Optional[str] = None
    query_params = params or {}

    # Map actions to backend paths (from v1 logic)
    if action_name == "school_attendance_summary":
        path = "/api/attendance/summary"
    elif action_name == "student_overview":
        path = "/api/attendance/students/overview"
    elif action_name == "student_attendance_report":
        if not student_id: return {"error": "student_id required"}
        path = f"/api/attendance/students/{student_id}/report"
    elif action_name == "student_attendance_stats":
        if not student_id: return {"error": "student_id required"}
        path = f"/api/attendance/students/{student_id}/stats"
    elif action_name == "my_attendance_records":
        path = "/api/attendance/me/records"
    elif action_name == "event_attendance_report":
        if not event_id: return {"error": "event_id required"}
        path = f"/api/attendance/events/{event_id}/report"
    elif action_name == "governance_dashboard_overview":
        if not governance_unit_id: return {"error": "governance_unit_id required"}
        path = f"/api/governance/units/{governance_unit_id}/dashboard-overview"

    if not path:
        return {"error": f"Unsupported report action: {action_name}"}

    headers = {"Authorization": authorization}
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.get(f"{BACKEND_API_BASE_URL}{path}", headers=headers, params=query_params)
            return resp.json()
        except Exception as e:
            return {"error": f"Report request failed: {str(e)}"}

@mcp.tool()
async def mcp_visualize(
    type: str,
    title: str,
    payload: Dict[str, Any],
    footer: Optional[str] = None
) -> str:
    """
    Renders a chart in the user interface.
    type: chart type, e.g. 'bar', 'line', 'pie', 'doughnut'
    title: title of the chart
    payload: standard Chart.js payload format: {'labels': [str], 'datasets': [{'label': str, 'data': [number]}]}
    Provides visualization strictly based on query results.
    """
    import json
    return json.dumps({
        "__aura_visual__": True,
        "type": type,
        "title": title,
        "payload": payload,
        "footer": footer or ""
    })

if __name__ == "__main__":
    mcp.run()

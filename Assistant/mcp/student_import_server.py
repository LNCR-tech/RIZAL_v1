"""Dedicated student bulk import MCP service."""

from __future__ import annotations

import csv
import io
import json
import os
import re
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException
from openpyxl import Workbook
from pydantic import BaseModel, Field

from policy import normalize_role


BACKEND_API_BASE_URL = os.getenv("BACKEND_API_BASE_URL")
EXPECTED_HEADERS = [
    "Student_ID",
    "Email",
    "Last Name",
    "First Name",
    "Middle Name",
    "Department",
    "Course",
]

HEADER_ALIASES = {
    "student_id": "Student_ID",
    "student id": "Student_ID",
    "id": "Student_ID",
    "email": "Email",
    "last_name": "Last Name",
    "last name": "Last Name",
    "lastname": "Last Name",
    "first_name": "First Name",
    "first name": "First Name",
    "firstname": "First Name",
    "middle_name": "Middle Name",
    "middle name": "Middle Name",
    "middlename": "Middle Name",
    "middle": "Middle Name",
    "department": "Department",
    "college": "Department",
    "course": "Course",
    "program": "Course",
}

app = FastAPI(title="MCP Student Import Service")


class ActionRequest(BaseModel):
    role: str | None = None
    roles: list[str] = Field(default_factory=list)
    action: str
    dataset_text: str | None = None
    dataset_format: str = "auto"
    preview_token: str | None = None
    job_id: str | None = None


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


def _require_import_role(body: ActionRequest) -> None:
    roles = _resolve_roles(body)
    if not any(role in {"admin", "campus_admin"} for role in roles):
        raise HTTPException(status_code=403, detail="admin or campus_admin role required for student import")


def _normalize_header(header: Any) -> str:
    return re.sub(r"\s+", " ", str(header or "").strip().lower())


def _detect_format(dataset_text: str, dataset_format: str) -> str:
    requested = (dataset_format or "auto").strip().lower()
    if requested in {"csv", "tsv", "json", "markdown"}:
        return requested
    stripped = dataset_text.lstrip()
    if stripped.startswith("[") or stripped.startswith("{"):
        return "json"
    first_line = next((line for line in dataset_text.splitlines() if line.strip()), "")
    if "|" in first_line and first_line.strip().startswith("|"):
        return "markdown"
    if "\t" in first_line:
        return "tsv"
    return "csv"


def _parse_delimited(dataset_text: str, delimiter: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(dataset_text), delimiter=delimiter)
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="dataset is missing a header row")
    rows: list[dict[str, str]] = []
    for row in reader:
        rows.append({str(key): "" if value is None else str(value) for key, value in row.items()})
    return rows


def _split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _parse_markdown(dataset_text: str) -> list[dict[str, str]]:
    lines = [line for line in dataset_text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise HTTPException(status_code=400, detail="markdown table must include header and at least one row")
    headers = _split_markdown_row(lines[0])
    separator = _split_markdown_row(lines[1])
    if not separator or not all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in separator):
        raise HTTPException(status_code=400, detail="invalid markdown table separator row")
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        values = _split_markdown_row(line)
        if len(values) < len(headers):
            values.extend([""] * (len(headers) - len(values)))
        rows.append(dict(zip(headers, values)))
    return rows


def _parse_json_rows(dataset_text: str) -> list[dict[str, str]]:
    try:
        data = json.loads(dataset_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSON dataset: {exc}") from exc
    if isinstance(data, dict):
        data = data.get("rows")
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="JSON dataset must be an array of objects")
    rows: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail="JSON dataset rows must be objects")
        rows.append({str(key): "" if value is None else str(value) for key, value in item.items()})
    return rows


def _canonicalize_rows(raw_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not raw_rows:
        raise HTTPException(status_code=400, detail="dataset has no rows")

    header_map: dict[str, str] = {}
    for header in raw_rows[0].keys():
        normalized = _normalize_header(header)
        mapped = HEADER_ALIASES.get(normalized)
        if mapped:
            header_map[header] = mapped

    missing_headers = [header for header in EXPECTED_HEADERS if header not in header_map.values()]
    if missing_headers:
        raise HTTPException(
            status_code=400,
            detail=f"dataset is missing required headers: {', '.join(missing_headers)}",
        )

    canonical_rows: list[dict[str, str]] = []
    for raw_row in raw_rows:
        canonical = {header: "" for header in EXPECTED_HEADERS}
        for source_key, value in raw_row.items():
            mapped = header_map.get(source_key)
            if mapped:
                canonical[mapped] = str(value).strip()
        canonical_rows.append(canonical)
    return canonical_rows


def _dataset_to_rows(dataset_text: str, dataset_format: str) -> tuple[str, list[dict[str, str]]]:
    detected_format = _detect_format(dataset_text, dataset_format)
    if detected_format == "json":
        raw_rows = _parse_json_rows(dataset_text)
    elif detected_format == "markdown":
        raw_rows = _parse_markdown(dataset_text)
    elif detected_format == "tsv":
        raw_rows = _parse_delimited(dataset_text, "\t")
    else:
        raw_rows = _parse_delimited(dataset_text, ",")
    return detected_format, _canonicalize_rows(raw_rows)


def _build_workbook_bytes(rows: list[dict[str, str]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Students"
    sheet.append(EXPECTED_HEADERS)
    for row in rows:
        sheet.append([row.get(header, "") for header in EXPECTED_HEADERS])
    output = io.BytesIO()
    workbook.save(output)
    workbook.close()
    output.seek(0)
    return output.read()


def _require_backend_api() -> str:
    base_url = (BACKEND_API_BASE_URL or "").strip().rstrip("/")
    if not base_url:
        raise HTTPException(
            status_code=503,
            detail="BACKEND_API_BASE_URL is required for student import actions",
        )
    return base_url


async def _backend_request(
    method: str,
    path: str,
    *,
    authorization: str,
    files: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_url = _require_backend_api()
    headers = {"Authorization": authorization}
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.request(
            method,
            f"{base_url}{path}",
            headers=headers,
            files=files,
            data=data,
        )
    if response.status_code >= 400:
        detail: Any
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise HTTPException(
            status_code=response.status_code,
            detail={"backend_error": detail, "path": path},
        )
    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"backend returned invalid JSON for {path}") from exc


async def _run_action_internal(body: ActionRequest, authorization: str | None) -> dict[str, Any]:
    action = body.action.strip().lower()

    if action == "expected_headers":
        return {
            "action": action,
            "expected_headers": EXPECTED_HEADERS,
            "accepted_formats": ["csv", "tsv", "json", "markdown"],
        }

    _require_import_role(body)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization bearer token is required for import actions")

    if action == "preview_import":
        if not body.dataset_text:
            raise HTTPException(status_code=400, detail="dataset_text is required for preview_import")
        detected_format, rows = _dataset_to_rows(body.dataset_text, body.dataset_format)
        workbook_bytes = _build_workbook_bytes(rows)
        result = await _backend_request(
            "POST",
            "/api/admin/import-students/preview",
            authorization=authorization,
            files={
                "file": (
                    "assistant_student_import.xlsx",
                    workbook_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        return {
            "action": action,
            "detected_format": detected_format,
            "normalized_row_count": len(rows),
            "result": result,
        }

    if action == "commit_import":
        preview_token = (body.preview_token or "").strip()
        if not preview_token:
            raise HTTPException(status_code=400, detail="preview_token is required for commit_import")
        result = await _backend_request(
            "POST",
            "/api/admin/import-students",
            authorization=authorization,
            data={"preview_token": preview_token},
        )
        return {
            "action": action,
            "preview_token": preview_token,
            "result": result,
        }

    if action == "clean_preview":
        preview_token = (body.preview_token or "").strip()
        if not preview_token:
            raise HTTPException(status_code=400, detail="preview_token is required for clean_preview")
        result = await _backend_request(
            "POST",
            f"/api/admin/import-preview-errors/{preview_token}/remove-invalid",
            authorization=authorization,
        )
        return {
            "action": action,
            "preview_token": preview_token,
            "result": result,
        }

    if action == "import_status":
        job_id = (body.job_id or "").strip()
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required for import_status")
        result = await _backend_request(
            "GET",
            f"/api/admin/import-status/{job_id}",
            authorization=authorization,
        )
        return {
            "action": action,
            "job_id": job_id,
            "result": result,
        }

    raise HTTPException(status_code=400, detail=f"unsupported student import action: {body.action}")


@app.post("/action")
async def run_action(
    body: ActionRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return await _run_action_internal(body, authorization)

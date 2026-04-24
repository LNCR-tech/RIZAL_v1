"""Use: Defines request and response data shapes for bulk import API data.
Where to use: Use this in routers and services when validating or returning bulk import API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ImportErrorItem(BaseModel):
    row: int
    error: str


class ImportJobCreateResponse(BaseModel):
    job_id: str
    status: str
    retried_from_job_id: Optional[str] = None


class RetryFailedRowsRequest(BaseModel):
    row_numbers: Optional[List[int]] = None


class ImportPreviewRow(BaseModel):
    row: int
    status: str
    errors: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    row_data: Optional[dict[str, Any]] = None


class ImportPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    can_commit: bool
    preview_token: Optional[str] = None
    rows: List[ImportPreviewRow] = Field(default_factory=list)


class ImportJobStatusResponse(BaseModel):
    job_id: str
    state: str
    total_rows: int
    processed_rows: int
    success_count: int
    failed_count: int
    percentage_completed: float
    estimated_time_remaining_seconds: Optional[int] = None
    errors: List[ImportErrorItem] = Field(default_factory=list)
    failed_report_download_url: Optional[str] = None

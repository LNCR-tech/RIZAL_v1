"""Top-level reports router wiring.

This router is mounted from `app.main` and exposes report endpoints under the
existing `/api/attendance/*` contracts.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.reports.attendance.router import router as attendance_reports_router
from app.reports.school.router import router as school_reports_router
from app.reports.student.router import router as student_reports_router

router = APIRouter(prefix="/attendance", tags=["attendance"])
router.include_router(attendance_reports_router)
router.include_router(student_reports_router)
router.include_router(school_reports_router)


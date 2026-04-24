"""Reporting routes for the attendance router package."""

from fastapi import APIRouter

from app.reports.attendance.router import router as attendance_report_router
from app.reports.school.router import router as school_report_router
from app.reports.student.router import router as student_report_router

router = APIRouter()
router.include_router(attendance_report_router)
router.include_router(student_report_router)
router.include_router(school_report_router)


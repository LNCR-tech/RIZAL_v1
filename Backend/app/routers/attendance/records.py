"""Legacy attendance records router.

Record/report endpoints were consolidated under `app.reports.*` and are
included by `attendance/reports.py`. This module remains as an empty router to
preserve the existing package wiring in `attendance/__init__.py`.
"""

from fastapi import APIRouter

router = APIRouter()


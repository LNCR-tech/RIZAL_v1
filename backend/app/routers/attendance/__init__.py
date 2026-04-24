"""Use: Handles attendance check-in and attendance action endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs attendance operational features.
Role: Router package. Reporting endpoints are now mounted from `app.reports.router`.
"""

from fastapi import APIRouter

from .check_in_out import router as check_in_out_router
from .overrides import router as overrides_router

router = APIRouter(prefix="/attendance", tags=["attendance"])
router.include_router(check_in_out_router)
router.include_router(overrides_router)

__all__ = ["router"]

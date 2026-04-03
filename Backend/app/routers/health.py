"""Use: Handles health and database pool status API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs health and database pool status features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_database_pool_snapshot
from app.core.dependencies import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    database_ok = True
    database_detail: str | None = None
    bind = db.get_bind()

    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        database_ok = False
        database_detail = str(exc)

    payload = {
        "status": "ok" if database_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "ok": database_ok,
            "detail": database_detail,
        },
        "pool": get_database_pool_snapshot(bind=bind),
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )

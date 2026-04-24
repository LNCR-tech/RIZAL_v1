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
from app.services.face_recognition import FaceRecognitionService

router = APIRouter(tags=["health"])
face_service = FaceRecognitionService()


def _database_probe(db: Session) -> tuple[bool, str | None]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return True, None


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    database_ok, database_detail = _database_probe(db)
    bind = db.get_bind()
    face_runtime = face_service.face_runtime_status(mode="single")

    payload = {
        "status": "ok" if database_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "ok": database_ok,
            "detail": database_detail,
        },
        "face_runtime": face_runtime,
        "readiness": {
            "ready": bool(database_ok and face_runtime.get("ready")),
            "database_ready": database_ok,
            "face_runtime_ready": bool(face_runtime.get("ready")),
        },
        "pool": get_database_pool_snapshot(bind=bind),
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )


@router.get("/health/readiness")
def readiness_check(db: Session = Depends(get_db)):
    database_ok, database_detail = _database_probe(db)
    face_runtime = face_service.face_runtime_status(mode="single")
    ready = bool(database_ok and face_runtime.get("ready"))

    payload = {
        "status": "ready" if ready else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "ok": database_ok,
            "detail": database_detail,
        },
        "face_runtime": face_runtime,
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )

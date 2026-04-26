"""Use: Starts the FastAPI app and registers all backend routers.
Where to use: Use this file when running the API server because it is the main application entry point.
Role: Application entry layer. It wires the app, middleware, static files, and routes together.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.middleware import MaxRequestBodySizeMiddleware, MutationRateLimitMiddleware
from app.reports.router import router as reports_router
from app.services.email_service import validate_email_delivery_on_startup
from app.services.face_recognition import FaceRecognitionService
from app.routers import (
    users,
    events,
    programs,
    departments,
    auth,
    attendance,
    school_settings,
    admin_import,
    school,
    audit_logs,
    notifications,
    security_center,
    subscription,
    governance,
    governance_hierarchy,
    face_recognition,
    public_attendance,
    health,
    sanctions,
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        validate_email_delivery_on_startup()
    except Exception as exc:
        logger.warning(
            "Email delivery startup check failed — continuing without email: %s", exc
        )
    if not settings.face_warmup_on_startup:
        logger.info("InsightFace startup warm-up is disabled by configuration.")
        yield
        return
    try:
        runtime_status = FaceRecognitionService().initialize_face_runtime(
            mode="single",
            background=True,
            trigger="startup",
        )
        logger.info(
            "InsightFace startup initialization requested (state=%s, reason=%s).",
            runtime_status.get("state", "unknown"),
            runtime_status.get("reason", "unknown"),
        )
    except Exception:
        # Face warm-up should not block API startup; registration endpoints still
        # return explicit runtime errors when the model is not ready yet.
        logger.exception("InsightFace startup warm-up probe failed.")
    yield


app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if settings.api_docs_enabled else None,
    redoc_url="/redoc" if settings.api_docs_enabled else None,
    openapi_url="/openapi.json" if settings.api_docs_enabled else None,
)

if settings.trusted_hosts and settings.trusted_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

app.add_middleware(MaxRequestBodySizeMiddleware)
app.add_middleware(MutationRateLimitMiddleware)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def include_api_router(router: APIRouter) -> None:
    app.include_router(router, prefix="/api")


# Include routers
app.include_router(auth.router)
include_api_router(users.router)
include_api_router(events.router)
include_api_router(programs.router)
include_api_router(departments.router)
include_api_router(attendance.router)
include_api_router(reports_router)
app.include_router(school_settings.router)
app.include_router(admin_import.router)
app.include_router(school.router)
app.include_router(audit_logs.router)
app.include_router(notifications.router)
include_api_router(security_center.router)
app.include_router(subscription.router)
app.include_router(governance.router)
app.include_router(governance_hierarchy.router)
include_api_router(face_recognition.router)
app.include_router(public_attendance.router)
app.include_router(health.router)
include_api_router(sanctions.router)

logo_storage_dir = Path(settings.school_logo_storage_dir)
logo_storage_dir.mkdir(parents=True, exist_ok=True)
app.mount(settings.school_logo_public_prefix, StaticFiles(directory=str(logo_storage_dir)), name="school-logos")

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Student Attendance System API",
        "private_api_prefix": "/api",
        "endpoints": {
            "users": "/api/users",
            "events": "/api/events",
            "programs": "/api/programs",
            "departments": "/api/departments",
            "attendance": "/api/attendance",
            "school_settings": "/api/school-settings",
            "admin_import": "/api/admin/import-students",
            "school_branding": "/api/school/me",
            "audit_logs": "/api/audit-logs",
            "notifications": "/api/notifications",
            "security": "/api/auth/security",
            "face": "/api/face",
            "public_attendance": "/public-attendance",
            "health": "/health",
            "subscription": "/api/subscription/me",
            "governance": "/api/governance/settings/me",
            "governance_hierarchy": "/api/governance/units",
            "sanctions": "/api/sanctions",
        }
    }

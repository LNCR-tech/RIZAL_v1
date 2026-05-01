"""Admin placeholder routes for security testing."""

from fastapi import APIRouter, Depends
from app.core.security import get_current_admin
from app.core.dependencies import get_db
from app.models.user import User
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/some-endpoint")
def admin_placeholder_endpoint(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Placeholder admin endpoint for security testing.
    
    Returns 401 for unauthenticated, 403 for non-admin, 200 for admin.
    """
    return {"status": "ok", "message": "Admin endpoint accessible"}

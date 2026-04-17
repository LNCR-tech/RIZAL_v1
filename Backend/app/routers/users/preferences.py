"""Per-user app preference routes for the user router package."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.security import get_current_application_user
from app.models.user import User as UserModel
from app.schemas.user_preference import UserAppPreferenceResponse, UserAppPreferenceUpdate
from app.services.user_preference_service import (
    get_or_create_user_app_preference,
    normalize_font_size_percent,
)

router = APIRouter()


@router.get("/preferences/me", response_model=UserAppPreferenceResponse)
def get_my_app_preferences(
    current_user: UserModel = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    pref = get_or_create_user_app_preference(db, user_id=current_user.id)
    db.commit()
    db.refresh(pref)
    return pref


@router.put("/preferences/me", response_model=UserAppPreferenceResponse)
def update_my_app_preferences(
    payload: UserAppPreferenceUpdate,
    current_user: UserModel = Depends(get_current_application_user),
    db: Session = Depends(get_db),
):
    pref = get_or_create_user_app_preference(db, user_id=current_user.id)

    if payload.dark_mode_enabled is not None:
        pref.dark_mode_enabled = bool(payload.dark_mode_enabled)
    if payload.font_size_percent is not None:
        pref.font_size_percent = normalize_font_size_percent(payload.font_size_percent)

    db.commit()
    db.refresh(pref)
    return pref

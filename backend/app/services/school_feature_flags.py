"""Use: Contains logic for checking school-level feature flags.
Where to use: Use this from routers or other services when school-specific feature availability must be checked.
Role: Service layer. It abstracts feature gating logic.
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from app.models.school import School


def privileged_face_verification_enabled_for_school(
    db: Session,
    school_id: int | None,
) -> bool:
    """Check if a school has privileged face verification enabled.
    
    Currently, this returns True for all schools if the global setting is enabled.
    In the future, this can be linked to subscription plans or specific school overrides.
    """
    if school_id is None:
        # Platform admins (global) are always allowed if the global flag is on.
        return True
        
    # We can eventually query a SchoolFeatureFlag table or check subscription here.
    # For now, we return True to maintain parity with the global setting.
    return True

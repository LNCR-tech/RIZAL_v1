from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.core.timezones import utc_now
from app.models.event import Event, EventTarget, EventTargetScope
from app.models.user import User
from app.services import auth_session
from app.services.event_eligibility_service import is_student_eligible_for_event
from app.services.event_geolocation import verify_event_geolocation_for_attendance


def _make_event(db_session, *, school_id, name="Automation Backlog Event", **overrides):
    """Create the smallest Event row needed by service-level workflow tests."""
    now = utc_now()
    event = Event(
        school_id=school_id,
        name=name,
        location="Automation Test Hall",
        start_datetime=now - timedelta(minutes=15),
        end_datetime=now + timedelta(hours=1),
        created_by_user_id=1,
        **overrides,
    )
    db_session.add(event)
    db_session.flush()
    return event


def test_event_targeting_accepts_matching_year_and_rejects_other_year(db_session):
    student = db_session.query(User).filter_by(email="student@test.com").first().student_profile
    student.student_status = "ACTIVE"
    student.year_level = 1

    matching_event = _make_event(
        db_session,
        school_id=student.school_id,
        name="Automation Matching Year Event",
    )
    matching_event.event_targets.append(
        EventTarget(
            school_id=student.school_id,
            scope_type=EventTargetScope.YEAR_LEVEL,
            year_level=1,
        )
    )

    blocked_event = _make_event(
        db_session,
        school_id=student.school_id,
        name="Automation Blocked Year Event",
    )
    blocked_event.event_targets.append(
        EventTarget(
            school_id=student.school_id,
            scope_type=EventTargetScope.YEAR_LEVEL,
            year_level=2,
        )
    )
    db_session.flush()

    # These assertions protect the event-targeting rule that decides who can attend.
    assert is_student_eligible_for_event(student, matching_event) == (True, None, None)
    eligible, code, message = is_student_eligible_for_event(student, blocked_event)
    assert eligible is False
    assert code == "STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE"
    assert "scope" in message.lower()


def test_attendance_geofence_accepts_inside_and_rejects_outside_location(db_session):
    event = _make_event(
        db_session,
        school_id=1,
        name="Automation Geofence Event",
        geo_latitude=14.5995,
        geo_longitude=120.9842,
        geo_radius_m=50,
        geo_required=True,
        geo_max_accuracy_m=30,
    )

    # Same coordinates should pass because the student is at the event marker.
    inside = verify_event_geolocation_for_attendance(
        event,
        latitude=14.5995,
        longitude=120.9842,
        accuracy_m=5,
    )
    assert inside is not None
    assert inside.ok is True

    # A clearly distant coordinate should be rejected before attendance is saved.
    with pytest.raises(HTTPException) as exc_info:
        verify_event_geolocation_for_attendance(
            event,
            latitude=14.6095,
            longitude=120.9842,
            accuracy_m=5,
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "event_geolocation_verification_failed"


def test_privileged_login_requires_face_when_mfa_policy_is_enabled(
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter_by(email="campus_admin@test.com").first()

    class Settings:
        privileged_face_verification_enabled = True

    class SecuritySetting:
        trusted_device_days = 14
        mfa_enabled = True

    # Patch only the policy seams so this stays a fast service test, not a face-engine test.
    monkeypatch.setattr(auth_session, "get_settings", lambda: Settings())
    monkeypatch.setattr(
        auth_session,
        "privileged_face_verification_enabled_for_school",
        lambda db, school_id: True,
    )
    monkeypatch.setattr(auth_session, "is_face_scan_bypass_enabled_for_user", lambda user: False)
    monkeypatch.setattr(
        auth_session,
        "get_or_create_user_security_setting",
        lambda db, user: SecuritySetting(),
    )

    response = auth_session.issue_login_token_response(db=db_session, user=user)

    assert response["face_verification_required"] is True
    assert response["face_verification_pending"] is True
    assert response["session_id"] is None


def test_privileged_face_bypass_returns_full_session_token(db_session, monkeypatch):
    user = db_session.query(User).filter_by(email="campus_admin@test.com").first()

    class Settings:
        privileged_face_verification_enabled = True

    class SecuritySetting:
        trusted_device_days = 14
        mfa_enabled = True

    monkeypatch.setattr(auth_session, "get_settings", lambda: Settings())
    monkeypatch.setattr(
        auth_session,
        "privileged_face_verification_enabled_for_school",
        lambda db, school_id: True,
    )
    monkeypatch.setattr(auth_session, "is_face_scan_bypass_enabled_for_user", lambda user: True)
    monkeypatch.setattr(
        auth_session,
        "get_or_create_user_security_setting",
        lambda db, user: SecuritySetting(),
    )
    monkeypatch.setattr(auth_session, "create_user_session", lambda *args, **kwargs: None)

    # Test-mode face bypass should keep login automation from needing real camera/face data.
    response = auth_session.issue_login_token_response(db=db_session, user=user)

    assert response["face_verification_required"] is False
    assert response["face_verification_pending"] is False
    assert response["session_id"]


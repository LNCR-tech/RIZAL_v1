"""Tests for Phase 9: event announcement notifications respect event_targets scope.

Covers:
- YEAR_LEVEL event notifies only matching year level students.
- COURSE_YEAR event notifies only matching course + year students.
- GRADUATED student does not receive notification.
- Out-of-scope student does not receive notification.
- Multi-school boundary is enforced (event from another school returns 404).
"""

from uuid import uuid4

import pytest
from app.models.event import Event, EventTarget, EventTargetScope
from app.models.user import User, UserRole, StudentProfile
from app.models.notifications import NotificationLog
from app.models.attendance import AttendanceMethodLookup, AttendanceStatusLookup
from app.utils.passwords import hash_password_bcrypt
from app.services.notification_center_service import dispatch_event_announcement_notifications
from app.core.timezones import utc_now
from datetime import timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _future_event(db, *, school_id, name="Test Announcement Event"):
    now = utc_now()
    event = Event(
        school_id=school_id,
        name=name,
        start_at=now + timedelta(hours=2),
        end_at=now + timedelta(hours=4),
        status="upcoming",
    )
    db.add(event)
    db.flush()
    return event


def _make_student(db, *, email, school_id, dept_id, prog_id, year_level, student_status="ACTIVE"):
    role = db.query(__import__("app.models.role", fromlist=["Role"]).Role).filter_by(code="student").first()
    user = User(
        email=email,
        school_id=school_id,
        first_name="Test",
        last_name="Student",
        password_hash=hash_password_bcrypt("TestPass123!"),
        must_change_password=False,
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    profile = StudentProfile(
        user_id=user.id,
        school_id=school_id,
        student_number=f"STU-{user.id}",
        department_id=dept_id,
        program_id=prog_id,
        year_level=year_level,
        student_status=student_status,
    )
    db.add(profile)
    db.flush()
    return user, profile


def _notification_count(db, *, user_id, category="event_announcement"):
    return (
        db.query(NotificationLog)
        .filter(
            NotificationLog.user_id == user_id,
            NotificationLog.category == category,
        )
        .count()
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def school_and_deps(db_session):
    from app.models.school import School, SchoolBranding, SchoolEventPolicy
    from app.models.department import Department
    from app.models.program import Program

    school = db_session.query(School).filter_by(school_code="TEST-001").first()
    dept = db_session.query(Department).filter_by(school_id=school.id, name="Test Department").first()
    prog = db_session.query(Program).filter_by(school_id=school.id, name="Test Program").first()
    return school, dept, prog


@pytest.fixture(scope="module")
def other_school(db_session):
    from app.models.school import School, SchoolBranding, SchoolEventPolicy

    s = db_session.query(School).filter_by(school_code="OTHER-001").first()
    if not s:
        s = School(school_code="OTHER-001", legal_name="Other School", display_name="Other School",
                   address="456 Other St", is_active=True)
        db_session.add(s)
        db_session.flush()
        db_session.add(SchoolBranding(school_id=s.id, primary_color="#000000"))
        db_session.add(SchoolEventPolicy(school_id=s.id, default_early_check_in_minutes=30,
                                         default_late_threshold_minutes=10, default_sign_out_grace_minutes=20))
        db_session.flush()
    return s


# ---------------------------------------------------------------------------
# Tests: service layer
# ---------------------------------------------------------------------------

def test_year_level_target_notifies_only_matching_year(db_session, school_and_deps):
    school, dept, prog = school_and_deps

    user_y2, profile_y2 = _make_student(
        db_session, email=f"y2_{utc_now().timestamp()}@test.com",
        school_id=school.id, dept_id=dept.id, prog_id=prog.id, year_level=2,
    )
    user_y3, profile_y3 = _make_student(
        db_session, email=f"y3_{utc_now().timestamp()}@test.com",
        school_id=school.id, dept_id=dept.id, prog_id=prog.id, year_level=3,
    )

    event = _future_event(db_session, school_id=school.id, name="Year2 Only Event")
    db_session.add(EventTarget(
        event_id=event.id,
        school_id=school.id,
        scope_type=EventTargetScope.YEAR_LEVEL,
        year_level=2,
    ))
    db_session.flush()

    before_y2 = _notification_count(db_session, user_id=user_y2.id)
    before_y3 = _notification_count(db_session, user_id=user_y3.id)

    result = dispatch_event_announcement_notifications(db_session, event=event)
    db_session.flush()

    assert _notification_count(db_session, user_id=user_y2.id) == before_y2 + 1
    assert _notification_count(db_session, user_id=user_y3.id) == before_y3  # not notified
    assert result["processed_users"] >= 1


def test_course_year_target_notifies_only_matching_course_and_year(db_session, school_and_deps):
    school, dept, prog = school_and_deps

    user_match, profile_match = _make_student(
        db_session, email=f"cy_match_{utc_now().timestamp()}@test.com",
        school_id=school.id, dept_id=dept.id, prog_id=prog.id, year_level=1,
    )
    user_wrong_year, profile_wrong_year = _make_student(
        db_session, email=f"cy_wrongyr_{utc_now().timestamp()}@test.com",
        school_id=school.id, dept_id=dept.id, prog_id=prog.id, year_level=2,
    )

    event = _future_event(db_session, school_id=school.id, name="CourseYear Event")
    db_session.add(EventTarget(
        event_id=event.id,
        school_id=school.id,
        scope_type=EventTargetScope.COURSE_YEAR,
        course_id=prog.id,
        year_level=1,
    ))
    db_session.flush()

    before_match = _notification_count(db_session, user_id=user_match.id)
    before_wrong = _notification_count(db_session, user_id=user_wrong_year.id)

    dispatch_event_announcement_notifications(db_session, event=event)
    db_session.flush()

    assert _notification_count(db_session, user_id=user_match.id) == before_match + 1
    assert _notification_count(db_session, user_id=user_wrong_year.id) == before_wrong


def test_graduated_student_does_not_receive_notification(db_session, school_and_deps):
    school, dept, prog = school_and_deps

    user_grad, _ = _make_student(
        db_session, email=f"grad_{utc_now().timestamp()}@test.com",
        school_id=school.id, dept_id=dept.id, prog_id=prog.id, year_level=4,
        student_status="GRADUATED",
    )

    event = _future_event(db_session, school_id=school.id, name="Grad Exclusion Event")
    db_session.add(EventTarget(
        event_id=event.id,
        school_id=school.id,
        scope_type=EventTargetScope.ALL,
    ))
    db_session.flush()

    before = _notification_count(db_session, user_id=user_grad.id)
    dispatch_event_announcement_notifications(db_session, event=event)
    db_session.flush()

    assert _notification_count(db_session, user_id=user_grad.id) == before


def test_inactive_student_does_not_receive_notification(db_session, school_and_deps):
    school, dept, prog = school_and_deps

    user_inactive, _ = _make_student(
        db_session, email=f"inactive_{utc_now().timestamp()}@test.com",
        school_id=school.id, dept_id=dept.id, prog_id=prog.id, year_level=1,
        student_status="INACTIVE",
    )

    event = _future_event(db_session, school_id=school.id, name="Inactive Exclusion Event")
    db_session.add(EventTarget(
        event_id=event.id,
        school_id=school.id,
        scope_type=EventTargetScope.ALL,
    ))
    db_session.flush()

    before = _notification_count(db_session, user_id=user_inactive.id)
    dispatch_event_announcement_notifications(db_session, event=event)
    db_session.flush()

    assert _notification_count(db_session, user_id=user_inactive.id) == before


def test_out_of_scope_student_does_not_receive_notification(db_session, school_and_deps):
    school, dept, prog = school_and_deps

    user_y5, _ = _make_student(
        db_session, email=f"y5_oos_{utc_now().timestamp()}@test.com",
        school_id=school.id, dept_id=dept.id, prog_id=prog.id, year_level=5,
    )

    event = _future_event(db_session, school_id=school.id, name="Year1 Only OOS Event")
    db_session.add(EventTarget(
        event_id=event.id,
        school_id=school.id,
        scope_type=EventTargetScope.YEAR_LEVEL,
        year_level=1,
    ))
    db_session.flush()

    before = _notification_count(db_session, user_id=user_y5.id)
    dispatch_event_announcement_notifications(db_session, event=event)
    db_session.flush()

    assert _notification_count(db_session, user_id=user_y5.id) == before


def test_all_scope_notifies_active_students_only(db_session, school_and_deps):
    school, dept, prog = school_and_deps

    user_active, _ = _make_student(
        db_session, email=f"all_active_{utc_now().timestamp()}@test.com",
        school_id=school.id, dept_id=dept.id, prog_id=prog.id, year_level=1,
        student_status="ACTIVE",
    )
    user_transferred, _ = _make_student(
        db_session, email=f"all_transferred_{utc_now().timestamp()}@test.com",
        school_id=school.id, dept_id=dept.id, prog_id=prog.id, year_level=1,
        student_status="TRANSFERRED",
    )

    event = _future_event(db_session, school_id=school.id, name="ALL Scope Active Only")
    db_session.add(EventTarget(
        event_id=event.id,
        school_id=school.id,
        scope_type=EventTargetScope.ALL,
    ))
    db_session.flush()

    before_active = _notification_count(db_session, user_id=user_active.id)
    before_transferred = _notification_count(db_session, user_id=user_transferred.id)

    dispatch_event_announcement_notifications(db_session, event=event)
    db_session.flush()

    assert _notification_count(db_session, user_id=user_active.id) == before_active + 1
    assert _notification_count(db_session, user_id=user_transferred.id) == before_transferred


def test_empty_participant_list_returns_zero_counts(db_session):
    from app.models.school import School

    empty_school = School(
        school_code=f"EMPTY-{uuid4().hex[:12].upper()}",
        legal_name="Empty Participants School",
        display_name="Empty Participants School",
        address="None",
        is_active=True,
    )
    db_session.add(empty_school)
    db_session.flush()

    event = _future_event(
        db_session,
        school_id=empty_school.id,
        name="No Participants Event",
    )
    db_session.add(EventTarget(
        event_id=event.id,
        school_id=empty_school.id,
        scope_type=EventTargetScope.YEAR_LEVEL,
        year_level=5,
    ))
    db_session.flush()

    try:
        result = dispatch_event_announcement_notifications(db_session, event=event)
        db_session.flush()

        assert result["processed_users"] == 0
        assert result["sent"] == 0
        assert result["failed"] == 0
        assert result["skipped"] == 0
    finally:
        db_session.delete(event)
        db_session.delete(empty_school)
        db_session.flush()


# ---------------------------------------------------------------------------
# Tests: HTTP endpoint — school boundary enforcement
# ---------------------------------------------------------------------------

def test_dispatch_announcement_endpoint_enforces_school_boundary(
    client, campus_admin_headers, db_session, other_school
):
    """campus_admin of school TEST-001 cannot announce an event from OTHER-001."""
    from app.models.department import Department
    from app.models.program import Program

    now = utc_now()
    other_event = Event(
        school_id=other_school.id,
        name="Other School Event",
        start_at=now + timedelta(hours=1),
        end_at=now + timedelta(hours=3),
        status="upcoming",
    )
    db_session.add(other_event)
    db_session.flush()
    db_session.add(EventTarget(
        event_id=other_event.id,
        school_id=other_school.id,
        scope_type=EventTargetScope.ALL,
    ))
    db_session.flush()

    r = client.post(
        f"/api/notifications/dispatch/event-announcement/{other_event.id}",
        headers=campus_admin_headers,
    )
    assert r.status_code == 404


def test_dispatch_announcement_endpoint_returns_summary(
    client, campus_admin_headers, db_session, school_and_deps
):
    school, dept, prog = school_and_deps
    now = utc_now()
    event = Event(
        school_id=school.id,
        name="HTTP Announcement Test",
        start_at=now + timedelta(hours=2),
        end_at=now + timedelta(hours=4),
        status="upcoming",
    )
    db_session.add(event)
    db_session.flush()
    db_session.add(EventTarget(
        event_id=event.id,
        school_id=school.id,
        scope_type=EventTargetScope.ALL,
    ))
    db_session.flush()

    r = client.post(
        f"/api/notifications/dispatch/event-announcement/{event.id}",
        headers=campus_admin_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "processed_users" in data
    assert "sent" in data
    assert "failed" in data
    assert "skipped" in data
    assert data["category"] == "event_announcement"


def test_dispatch_announcement_requires_admin(client, student_headers, db_session, school_and_deps):
    school, dept, prog = school_and_deps
    now = utc_now()
    event = Event(
        school_id=school.id,
        name="RBAC Test Event",
        start_at=now + timedelta(hours=2),
        end_at=now + timedelta(hours=4),
        status="upcoming",
    )
    db_session.add(event)
    db_session.flush()

    r = client.post(
        f"/api/notifications/dispatch/event-announcement/{event.id}",
        headers=student_headers,
    )
    assert r.status_code == 403


def test_dispatch_announcement_requires_auth(client, db_session, school_and_deps):
    school, _, _ = school_and_deps
    now = utc_now()
    event = Event(
        school_id=school.id,
        name="Auth Test Event",
        start_at=now + timedelta(hours=2),
        end_at=now + timedelta(hours=4),
        status="upcoming",
    )
    db_session.add(event)
    db_session.flush()

    r = client.post(f"/api/notifications/dispatch/event-announcement/{event.id}")
    assert r.status_code == 401


def test_dispatch_announcement_404_for_nonexistent_event(client, campus_admin_headers):
    r = client.post(
        "/api/notifications/dispatch/event-announcement/999999999",
        headers=campus_admin_headers,
    )
    assert r.status_code == 404

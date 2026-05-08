"""Tests for Phase 12: rejected scan attempts are audited via SchoolAuditLog.

Covers:
- Rejected out-of-scope scan creates a SchoolAuditLog row with action='attendance_scan_rejected'.
- Rejected scan does NOT create an AttendanceRecord.
- Rejected scan does NOT appear in normal attendance reports.
- Accepted scan behavior is unchanged (no audit row, attendance record created).
- _log_rejected_scan_attempt is fault-tolerant (DB error does not propagate).
"""

import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.models.school import SchoolAuditLog
from app.models.attendance import Attendance as AttendanceModel
from app.models.event import Event, EventTarget, EventTargetScope
from app.models.user import StudentProfile, User
from app.core.timezones import utc_now
from app.routers.attendance.shared import (
    _log_rejected_scan_attempt,
    _ensure_student_is_event_participant_with_audit,
)
from app.services.event_eligibility_service import is_student_eligible_for_event
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Unit tests: _log_rejected_scan_attempt
# ---------------------------------------------------------------------------

class TestLogRejectedScanAttempt:
    def test_writes_audit_log_row(self, db_session):
        from app.models.school import School
        school = db_session.query(School).filter_by(school_code="TEST-001").first()

        before_count = (
            db_session.query(SchoolAuditLog)
            .filter(
                SchoolAuditLog.school_id == school.id,
                SchoolAuditLog.action == "attendance_scan_rejected",
            )
            .count()
        )

        _log_rejected_scan_attempt(
            db_session,
            school_id=school.id,
            scanner_user_id=None,
            event_id=999,
            student_profile_id=888,
            attempt_type="SIGN_IN",
            reason_code="STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE",
            reason_message="Student is not included in this event scope.",
        )
        db_session.flush()

        after_count = (
            db_session.query(SchoolAuditLog)
            .filter(
                SchoolAuditLog.school_id == school.id,
                SchoolAuditLog.action == "attendance_scan_rejected",
            )
            .count()
        )
        assert after_count == before_count + 1

    def test_audit_row_has_correct_fields(self, db_session):
        from app.models.school import School
        school = db_session.query(School).filter_by(school_code="TEST-001").first()

        _log_rejected_scan_attempt(
            db_session,
            school_id=school.id,
            scanner_user_id=None,
            event_id=777,
            student_profile_id=666,
            attempt_type="MANUAL",
            reason_code="STUDENT_NOT_ACTIVE",
            reason_message="Only ACTIVE students can participate.",
        )
        db_session.flush()

        row = (
            db_session.query(SchoolAuditLog)
            .filter(
                SchoolAuditLog.school_id == school.id,
                SchoolAuditLog.action == "attendance_scan_rejected",
                SchoolAuditLog.status == "rejected",
            )
            .order_by(SchoolAuditLog.id.desc())
            .first()
        )
        assert row is not None
        assert row.status == "rejected"
        details = json.loads(row.details)
        assert details["result"] == "REJECTED"
        assert details["attempt_type"] == "MANUAL"
        assert details["reason_code"] == "STUDENT_NOT_ACTIVE"
        assert details["event_id"] == 777
        assert details["student_profile_id"] == 666

    def test_db_error_does_not_propagate(self, db_session):
        """Audit logging must never break the main request path."""
        bad_db = MagicMock()
        bad_db.add.side_effect = Exception("DB exploded")

        # Should not raise
        _log_rejected_scan_attempt(
            bad_db,
            school_id=1,
            scanner_user_id=None,
            event_id=1,
            student_profile_id=1,
            attempt_type="SIGN_IN",
            reason_code="STUDENT_NOT_ACTIVE",
            reason_message="test",
        )


# ---------------------------------------------------------------------------
# Unit tests: _ensure_student_is_event_participant_with_audit
# ---------------------------------------------------------------------------

class TestEnsureStudentIsEventParticipantWithAudit:
    def _make_student(self, school_id, year_level=1, student_status="ACTIVE"):
        student = MagicMock(spec=StudentProfile)
        student.id = 42
        student.school_id = school_id
        student.year_level = year_level
        student.student_status = student_status
        student.department_id = 1
        student.program_id = 1
        return student

    def _make_event(self, school_id, scope=EventTargetScope.ALL):
        event = MagicMock(spec=Event)
        event.id = 10
        event.school_id = school_id
        target = MagicMock()
        target.scope_type = scope
        target.year_level = None
        target.department_id = None
        target.course_id = None
        event.event_targets = [target]
        event.programs = []
        event.departments = []
        return event

    def test_eligible_student_does_not_raise(self, db_session):
        from app.models.school import School
        school = db_session.query(School).filter_by(school_code="TEST-001").first()
        student = self._make_student(school.id)
        event = self._make_event(school.id, scope=EventTargetScope.ALL)

        # Should not raise
        _ensure_student_is_event_participant_with_audit(
            db_session,
            student=student,
            event=event,
            school_id=school.id,
            scanner_user_id=None,
            attempt_type="SIGN_IN",
        )

    def test_ineligible_student_raises_403(self, db_session):
        from app.models.school import School
        school = db_session.query(School).filter_by(school_code="TEST-001").first()
        # Student from a different school
        student = self._make_student(school_id=school.id + 9999)
        event = self._make_event(school.id, scope=EventTargetScope.ALL)

        with pytest.raises(HTTPException) as exc_info:
            _ensure_student_is_event_participant_with_audit(
                db_session,
                student=student,
                event=event,
                school_id=school.id,
                scanner_user_id=None,
                attempt_type="SIGN_IN",
            )
        assert exc_info.value.status_code == 403

    def test_ineligible_student_creates_audit_log(self, db_session):
        from app.models.school import School
        school = db_session.query(School).filter_by(school_code="TEST-001").first()
        student = self._make_student(school_id=school.id + 9999)
        event = self._make_event(school.id, scope=EventTargetScope.ALL)

        before = (
            db_session.query(SchoolAuditLog)
            .filter(
                SchoolAuditLog.school_id == school.id,
                SchoolAuditLog.action == "attendance_scan_rejected",
            )
            .count()
        )

        with pytest.raises(HTTPException):
            _ensure_student_is_event_participant_with_audit(
                db_session,
                student=student,
                event=event,
                school_id=school.id,
                scanner_user_id=None,
                attempt_type="SIGN_IN",
            )
        db_session.flush()

        after = (
            db_session.query(SchoolAuditLog)
            .filter(
                SchoolAuditLog.school_id == school.id,
                SchoolAuditLog.action == "attendance_scan_rejected",
            )
            .count()
        )
        assert after == before + 1


# ---------------------------------------------------------------------------
# Integration tests: HTTP endpoints
# ---------------------------------------------------------------------------

def _future_event_payload(name="Audit Test Event"):
    now = datetime.now(timezone.utc)
    return {
        "name": name,
        "start_datetime": (now - timedelta(minutes=5)).isoformat(),
        "end_datetime": (now + timedelta(hours=3)).isoformat(),
        "location": "Test Hall",
        "event_targets": [{"scope_type": "YEAR_LEVEL", "year_level": 5}],
    }


@pytest.fixture(scope="module")
def year5_only_event_id(client, campus_admin_headers):
    """Create an event that only targets year-level 5 students."""
    r = client.post("/api/events/", headers=campus_admin_headers, json=_future_event_payload())
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_rejected_scan_does_not_create_attendance_record(
    client, campus_admin_headers, db_session, year5_only_event_id
):
    """The test student is year_level=1, so they are out of scope for a year_level=5 event."""
    student = db_session.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(User.email == "student@test.com").first()

    if student is None:
        pytest.skip("Test student not found")

    before_count = (
        db_session.query(AttendanceModel)
        .filter(AttendanceModel.event_id == year5_only_event_id)
        .count()
    )

    r = client.post(
        "/api/attendance/face-scan",
        headers=campus_admin_headers,
        params={"event_id": year5_only_event_id, "student_id": student.student_number},
    )
    # Must be rejected (403 = out of scope)
    assert r.status_code == 403

    after_count = (
        db_session.query(AttendanceModel)
        .filter(AttendanceModel.event_id == year5_only_event_id)
        .count()
    )
    assert after_count == before_count, "Rejected scan must not create an attendance record"


def test_rejected_scan_creates_audit_log(
    client, campus_admin_headers, db_session, year5_only_event_id
):
    """A rejected face-scan attempt must produce a SchoolAuditLog row."""
    from app.models.school import School
    school = db_session.query(School).filter_by(school_code="TEST-001").first()

    student = db_session.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(User.email == "student@test.com").first()

    if student is None:
        pytest.skip("Test student not found")

    before = (
        db_session.query(SchoolAuditLog)
        .filter(
            SchoolAuditLog.school_id == school.id,
            SchoolAuditLog.action == "attendance_scan_rejected",
        )
        .count()
    )

    r = client.post(
        "/api/attendance/face-scan",
        headers=campus_admin_headers,
        params={"event_id": year5_only_event_id, "student_id": student.student_number},
    )
    assert r.status_code == 403

    after = (
        db_session.query(SchoolAuditLog)
        .filter(
            SchoolAuditLog.school_id == school.id,
            SchoolAuditLog.action == "attendance_scan_rejected",
        )
        .count()
    )
    assert after == before + 1


def test_rejected_scan_not_in_attendance_report(
    client, campus_admin_headers, db_session, year5_only_event_id
):
    """Rejected scans must not appear in the event attendance report."""
    r = client.get(
        f"/api/attendance/events/{year5_only_event_id}/report",
        headers=campus_admin_headers,
    )
    assert r.status_code == 200
    data = r.json()
    # The test student (year_level=1) was rejected; they must not appear as an attendee.
    assert data["attendees"] == 0


def test_accepted_scan_behavior_unchanged(client, campus_admin_headers, db_session):
    """An accepted scan still creates an attendance record and no audit rejection row."""
    from app.models.school import School
    school = db_session.query(School).filter_by(school_code="TEST-001").first()

    now = datetime.now(timezone.utc)
    # Create an ALL-scope event so the test student (year_level=1) is eligible
    r = client.post("/api/events/", headers=campus_admin_headers, json={
        "name": "Accepted Scan Test Event",
        "start_datetime": (now - timedelta(minutes=5)).isoformat(),
        "end_datetime": (now + timedelta(hours=3)).isoformat(),
        "location": "Test Hall",
        "event_targets": [{"scope_type": "ALL"}],
    })
    assert r.status_code in (200, 201), r.text
    event_id = r.json()["id"]

    student = db_session.query(StudentProfile).join(
        User, StudentProfile.user_id == User.id
    ).filter(User.email == "student@test.com").first()

    if student is None:
        pytest.skip("Test student not found")

    before_attendance = (
        db_session.query(AttendanceModel)
        .filter(AttendanceModel.event_id == event_id)
        .count()
    )
    before_rejected = (
        db_session.query(SchoolAuditLog)
        .filter(
            SchoolAuditLog.school_id == school.id,
            SchoolAuditLog.action == "attendance_scan_rejected",
        )
        .count()
    )

    r2 = client.post(
        "/api/attendance/face-scan",
        headers=campus_admin_headers,
        params={"event_id": event_id, "student_id": student.student_number},
    )
    assert r2.status_code == 200, r2.text

    after_attendance = (
        db_session.query(AttendanceModel)
        .filter(AttendanceModel.event_id == event_id)
        .count()
    )
    after_rejected = (
        db_session.query(SchoolAuditLog)
        .filter(
            SchoolAuditLog.school_id == school.id,
            SchoolAuditLog.action == "attendance_scan_rejected",
        )
        .count()
    )

    assert after_attendance == before_attendance + 1, "Accepted scan must create attendance record"
    assert after_rejected == before_rejected, "Accepted scan must not create a rejection audit row"

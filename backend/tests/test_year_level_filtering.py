from datetime import datetime, timedelta, timezone

from app.models.event import Event
from app.models.user import StudentProfile, User
from app.services.event_eligibility_service import is_student_eligible_for_event


def _future_event_payload(name, targets):
    now = datetime.now(timezone.utc)
    return {
        "name": name,
        "start_datetime": (now + timedelta(hours=2)).isoformat(),
        "end_datetime": (now + timedelta(hours=4)).isoformat(),
        "location": "Year Filter Hall",
        "event_targets": targets,
    }


def _student_profile_by_email(db_session, email):
    profile = (
        db_session.query(StudentProfile)
        .join(User, StudentProfile.user_id == User.id)
        .filter(User.email == email)
        .first()
    )
    assert profile is not None, f"Missing deterministic student profile for {email}"
    return profile


def test_year_level_event_created_through_api_filters_students_by_year(
    client,
    campus_admin_headers,
    db_session,
):
    # This exact workflow test creates a backend event scoped to Year 2 and
    # verifies the event eligibility service accepts only matching students.
    response = client.post(
        "/api/events/",
        headers=campus_admin_headers,
        json=_future_event_payload(
            "API Year 2 Filtering Event",
            [{"scope_type": "YEAR_LEVEL", "year_level": 2}],
        ),
    )
    assert response.status_code in (200, 201), response.text
    data = response.json()
    targets = data.get("event_targets", [])
    assert len(targets) == 1
    assert targets[0]["scope_type"] == "YEAR_LEVEL"
    assert targets[0]["year_level"] == 2

    event = db_session.query(Event).filter_by(id=data["id"]).first()
    assert event is not None

    year_two_student = _student_profile_by_email(db_session, "student_year2@test.com")
    year_one_student = _student_profile_by_email(db_session, "student@test.com")

    assert is_student_eligible_for_event(year_two_student, event) == (True, None, None)
    eligible, code, message = is_student_eligible_for_event(year_one_student, event)
    assert eligible is False
    assert code == "STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE"
    assert "scope" in message.lower()


def test_course_year_event_requires_matching_course_and_year(
    client,
    campus_admin_headers,
    db_session,
):
    # This exact workflow test protects the combined course + year filter:
    # matching course is not enough unless the year level also matches.
    year_two_student = _student_profile_by_email(db_session, "student_year2@test.com")
    year_five_student = _student_profile_by_email(db_session, "student_year5@test.com")

    response = client.post(
        "/api/events/",
        headers=campus_admin_headers,
        json=_future_event_payload(
            "API Course Year Filtering Event",
            [
                {
                    "scope_type": "COURSE_YEAR",
                    "course_id": year_two_student.program_id,
                    "year_level": year_two_student.year_level,
                }
            ],
        ),
    )
    assert response.status_code in (200, 201), response.text

    event = db_session.query(Event).filter_by(id=response.json()["id"]).first()
    assert event is not None

    assert is_student_eligible_for_event(year_two_student, event) == (True, None, None)
    eligible, code, message = is_student_eligible_for_event(year_five_student, event)
    assert eligible is False
    assert code == "STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE"
    assert "scope" in message.lower()

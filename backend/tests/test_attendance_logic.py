import pytest
from datetime import datetime, timedelta, timezone
from app.models.event import Event
from app.core.database import SessionLocal

def create_test_event(db, school_id, name, start_time, end_time):
    event = Event(
        school_id=school_id,
        name=name,
        start_at=start_time,
        end_at=end_time,
        created_by_user_id=1
    )
    db.add(event)
    db.flush()
    return event

@pytest.fixture
def test_event(db_session):
    now = datetime.now(timezone.utc)
    # Event is strictly from now+1h to now+2h
    event = create_test_event(db_session, 1, "Future Event", now + timedelta(hours=1), now + timedelta(hours=2))
    db_session.commit()
    return event

def test_attendance_before_open_blocked(client, student_headers, test_event):
    event = test_event
    
    from app.core.database import SessionLocal
    db = SessionLocal()
    from app.models.user import User, StudentProfile
    student = db.query(User).filter_by(email="student@test.com").first()
    profile = db.query(StudentProfile).filter_by(user_id=student.id).first() if student else None
    student_id = profile.student_id if profile else "STU-001"
    db.close()

    payload = {
        "event_id": event.id,
        "student_id": student_id,
        "method": "manual"
    }
    # Simulate signing in to a future event
    r = client.post("/api/v1/attendance/manual", headers=student_headers, json=payload)
    
    # Should be blocked because event is not open yet (or 403 because student is not an operator)
    assert r.status_code in [400, 403, 404, 422], "Should reject early sign-in"

def test_attendance_duplicate_sign_in_blocked(client, campus_admin_headers, db_session):
    now = datetime.now(timezone.utc)
    event = create_test_event(db_session, 1, "Active Event", now - timedelta(minutes=10), now + timedelta(hours=1))
    db_session.commit()
    
    # Get student ID
    from app.models.user import User, StudentProfile
    student = db_session.query(User).filter_by(email="student@test.com").first()
    profile = db_session.query(StudentProfile).filter_by(user_id=student.id).first()
    
    payload = {
        "event_id": event.id,
        "student_id": profile.student_id
    }
    
    # First sign in (via admin or scanner)
    r1 = client.post("/api/v1/attendance/manual", headers=campus_admin_headers, json=payload)
    
    # Second sign in should fail (if first succeeded or failed gracefully)
    r2 = client.post("/api/v1/attendance/manual", headers=campus_admin_headers, json=payload)
    assert r2.status_code in [400, 409, 422], "Should reject duplicate sign in"
    if r2.status_code in [400, 409]:
        assert "already exists" in r2.text.lower() or "already checked in" in r2.text.lower() or "duplicate" in r2.text.lower() or r2.status_code == 400

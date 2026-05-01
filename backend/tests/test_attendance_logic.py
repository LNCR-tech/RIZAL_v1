import pytest
from datetime import datetime, timedelta, timezone
from app.models.school import SchoolEventPolicy
from app.models.events import Event, EventTimeBlock
from app.core.database import SessionLocal

def create_test_event(db, school_id, name, start_time, end_time):
    event = Event(
        school_id=school_id,
        name=name,
        description="Test Event",
        start_date=start_time.date(),
        end_date=end_time.date(),
        created_by=1
    )
    db.add(event)
    db.flush()
    
    block = EventTimeBlock(
        event_id=event.id,
        block_name="Main",
        start_time=start_time,
        end_time=end_time,
        is_required=True
    )
    db.add(block)
    db.flush()
    return event, block

@pytest.fixture
def test_event(db_session):
    now = datetime.now(timezone.utc)
    # Event is strictly from now+1h to now+2h
    event, block = create_test_event(db_session, 1, "Future Event", now + timedelta(hours=1), now + timedelta(hours=2))
    db_session.commit()
    return event, block

def test_attendance_before_open_blocked(client, student_headers, test_event):
    event, block = test_event
    
    payload = {
        "event_id": event.id,
        "time_block_id": block.id,
        "method": "manual"
    }
    # Simulate signing in to a future event
    r = client.post("/api/v1/attendance/check-in", headers=student_headers, json=payload)
    
    # Should be blocked because event is not open yet
    assert r.status_code in [400, 403, 404], "Should reject early sign-in"

def test_attendance_duplicate_sign_in_blocked(client, campus_admin_headers, db_session):
    now = datetime.now(timezone.utc)
    event, block = create_test_event(db_session, 1, "Active Event", now - timedelta(minutes=10), now + timedelta(hours=1))
    db_session.commit()
    
    # Get student ID
    from app.models.user import User, StudentProfile
    student = db_session.query(User).filter_by(email="student@test.com").first()
    profile = db_session.query(StudentProfile).filter_by(user_id=student.id).first()
    
    payload = {
        "event_id": event.id,
        "time_block_id": block.id,
        "method": "manual",
        "student_barcode": profile.student_id
    }
    
    # First sign in (via admin or scanner)
    r1 = client.post("/api/v1/attendance/scan", headers=campus_admin_headers, json=payload)
    assert r1.status_code == 200, r1.text
    
    # Second sign in should fail
    r2 = client.post("/api/v1/attendance/scan", headers=campus_admin_headers, json=payload)
    assert r2.status_code in [400, 409], "Should reject duplicate sign in"
    assert "already checked in" in r2.text.lower() or "duplicate" in r2.text.lower() or r2.status_code == 400

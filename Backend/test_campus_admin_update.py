import asyncio
from datetime import datetime
from app.models.role import Role
from app.models.user import User as UserModel
from app.models.event import Event as EventModel
from app.schemas.event import EventUpdate
from app.routers.events.crud import update_event
from app.database import SessionLocal

def test_update():
    db = SessionLocal()
    try:
        current_user = db.query(UserModel).filter(UserModel.roles.any(Role.name == "campus_admin")).first()
        if not current_user:
            print("No campus admin found")
            return

        db_event = db.query(EventModel).filter(EventModel.school_id == current_user.school_id).first()
        if not db_event:
            print("No events found for school")
            return

        print(f"Testing on event {db_event.id} with user {current_user.id}")

        update_payload = EventUpdate(
            name="Hard Hatting Ceremony",
            location="University Covered Court",
            geo_latitude=10.0,
            geo_longitude=10.0,
            geo_radius_m=30.0,
            geo_max_accuracy_m=50.0,
            geo_required=False,
            # include a valid forward time to avoid the "start time in past" error
            start_datetime=datetime(2027, 4, 11, 8, 0, 0),
            end_datetime=datetime(2027, 4, 11, 12, 0, 0)
        )

        try:
            updated = update_event(
                event_id=db_event.id,
                event_update=update_payload,
                governance_context=None,
                db=db,
                current_user=current_user,
            )
            print("Update successful! New ID:", updated.id)
        except Exception as e:
            print("Failed inner:", repr(e))
    finally:
        db.close()

if __name__ == "__main__":
    test_update()

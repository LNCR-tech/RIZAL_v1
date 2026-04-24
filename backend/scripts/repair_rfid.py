import sys
import os

# Ensure we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from sqlalchemy import text

def repair_rfid_records():
    """Update all 'rfid' attendance records to 'face_scan' for schema compatibility."""
    db = SessionLocal()
    try:
        print("Starting Database Repair: Migrating 'rfid' -> 'face_scan'...")
        # Use direct SQL for maximum speed on 1,000,000+ rows
        result = db.execute(text("UPDATE attendances SET method = 'face_scan' WHERE method = 'rfid'"))
        db.commit()
        print(f"Repair Successful! {result.rowcount} records updated in seconds.")
    except Exception as e:
        print(f"Repair Failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    repair_rfid_records()


import os
import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path with priority
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.models.user import User
from app.models.platform_features import UserFaceProfile
from app.core.config import get_settings

def reset_face_profile(email: str):
    """
    Deletes the face profile for a user with the given email.
    """
    settings = get_settings()
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as session:
        # Find the user by email
        user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()

        if not user:
            print(f"No user found with email: {email}")
            return

        # Find and delete the face profile
        face_profile = session.execute(select(UserFaceProfile).where(UserFaceProfile.user_id == user.id)).scalar_one_or_none()

        if not face_profile:
            print(f"No face profile found for user: {email}")
            return

        session.delete(face_profile)
        session.commit()
        print(f"Face profile for {email} has been reset.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python reset_face_profile.py <email>")
        sys.exit(1)

    email_to_reset = sys.argv[1]
    reset_face_profile(email_to_reset)

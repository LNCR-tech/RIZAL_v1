# user_face_profiles table has been dropped in favour of student_face_embeddings.
# This file is kept as a stub so existing imports don't hard-crash during the transition.

from app.models.base import Base
from sqlalchemy import BigInteger, Column


class UserFaceRecognitionProfile(Base):
    """Stub — table dropped, kept for import compatibility only."""
    __tablename__ = "user_face_profiles"
    __table_args__ = {"extend_existing": True}
    user_id = Column(BigInteger, primary_key=True)

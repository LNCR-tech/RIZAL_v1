"""Use: Defines database models for face profiles and face verification records.
Where to use: Use this when the backend needs to store or load face profiles and face verification records data.
Role: Model layer. It maps Python objects to database tables and relationships.
"""

from app.models.platform_features import UserFaceProfile

UserFaceRecognitionProfile = UserFaceProfile

__all__ = ["UserFaceProfile", "UserFaceRecognitionProfile"]

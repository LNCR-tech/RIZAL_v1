"""Use: Defines database models for role records and role permissions.
Where to use: Use this when the backend needs to store or load role records and role permissions data.
Role: Model layer. It maps Python objects to database tables and relationships.
"""

from sqlalchemy import Column, Integer, String
from app.models.base import Base

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
"""Use: Defines database models for academic departments.
Where to use: Use this when the backend needs to store or load academic departments data.
Role: Model layer. It maps Python objects to database tables and relationships.
"""

# app/models/department.py
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.associations import program_department_association, event_department_association

class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_departments_school_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), index=True, nullable=True)
    name = Column(String, nullable=False)

    # Relationships
    programs = relationship(
        "Program", 
        secondary=program_department_association,
        back_populates="departments",
    )
    events = relationship(
        "Event",
        secondary=event_department_association,
        back_populates="departments",
    )
    school = relationship("School")

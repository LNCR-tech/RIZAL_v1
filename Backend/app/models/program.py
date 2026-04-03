"""Use: Defines database models for academic programs.
Where to use: Use this when the backend needs to store or load academic programs data.
Role: Model layer. It maps Python objects to database tables and relationships.
"""

# app/models/program.py
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.associations import program_department_association, event_program_association

class Program(Base):
    __tablename__ = "programs"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_programs_school_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), index=True, nullable=True)
    name = Column(String, nullable=False)

    # Relationships
    departments = relationship(
        "Department",
        secondary=program_department_association,
        back_populates="programs",
    )
    events = relationship(
        "Event",
        secondary=event_program_association,
        back_populates="programs",
    )
    school = relationship("School")

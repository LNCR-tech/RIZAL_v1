from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.associations import program_departments, event_departments


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="departments_school_id_name_key"),
    )

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)

    school = relationship("School")
    programs = relationship("Program", secondary=program_departments, back_populates="departments")
    events = relationship("Event", secondary=event_departments, back_populates="departments")

from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.associations import program_departments, event_programs


class Program(Base):
    __tablename__ = "programs"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="programs_school_id_name_key"),
    )

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)

    school = relationship("School")
    departments = relationship("Department", secondary=program_departments, back_populates="programs")
    events = relationship("Event", secondary=event_programs, back_populates="programs")

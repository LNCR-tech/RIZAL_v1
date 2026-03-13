from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.models.base import Base
from app.models.associations import event_department_association, event_program_association, event_ssg_association

class EventStatus(PyEnum):
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    geo_latitude = Column(Float, nullable=True)
    geo_longitude = Column(Float, nullable=True)
    geo_radius_m = Column(Float, nullable=True)
    geo_required = Column(Boolean, nullable=False, default=False)
    geo_max_accuracy_m = Column(Float, nullable=True)
    late_threshold_minutes = Column(Integer, nullable=False, default=0)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    status = Column(Enum(EventStatus), nullable=False, default=EventStatus.UPCOMING)
    
    
    # Many-to-many relationships
    departments = relationship(
        "Department", 
        secondary=event_department_association, 
        back_populates="events",
       
    )
    programs = relationship(
        "Program", 
        secondary=event_program_association, 
        back_populates="events",
       
    )
     # Add this relationship
    ssg_members = relationship(
        "SSGProfile", 
        secondary=event_ssg_association,
        back_populates="assigned_events",
        
    )
    attendances = relationship(
       "Attendance",
       back_populates="event",
       cascade="all, delete-orphan"
    )
    school = relationship("School", back_populates="events")

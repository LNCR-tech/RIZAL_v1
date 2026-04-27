from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.timezones import utc_now
from app.models.base import Base
from app.utils.passwords import hash_password_bcrypt, verify_password_bcrypt


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), index=True, nullable=True)
    email = Column(Text, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    prefix = Column(Text, nullable=True)
    first_name = Column(Text, nullable=True)
    middle_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    suffix = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    must_change_password = Column(Boolean, default=True, nullable=False)
    should_prompt_password_change = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    school = relationship("School", back_populates="users")
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserRole.user_id")
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty_profile = relationship("FacultyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        self.password_hash = hash_password_bcrypt(password)

    def check_password(self, password: str) -> bool:
        return verify_password_bcrypt(password, self.password_hash)


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    assigned_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user = relationship("User", back_populates="roles", foreign_keys=[user_id])
    role = relationship("Role")


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    __table_args__ = (
        UniqueConstraint("school_id", "student_number", name="student_profiles_school_id_student_number_key"),
    )

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=True)
    school_id = Column(BigInteger, ForeignKey("schools.id", ondelete="CASCADE"), index=True, nullable=False)
    student_number = Column(Text, nullable=False, index=True)
    department_id = Column(BigInteger, ForeignKey("departments.id", ondelete="RESTRICT"), index=True, nullable=True)
    program_id = Column(BigInteger, ForeignKey("programs.id", ondelete="RESTRICT"), index=True, nullable=True)
    year_level = Column(BigInteger, nullable=False, default=1)
    section = Column(Text, nullable=True, index=True)
    rfid_tag = Column(Text, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="student_profile")
    school = relationship("School", back_populates="student_profiles")
    department = relationship("Department")
    program = relationship("Program")
    attendance_records = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")

    # Compatibility property — old code used student_id, new schema uses student_number
    @property
    def student_id(self) -> str | None:
        return self.student_number

    @student_id.setter
    def student_id(self, value: str) -> None:
        self.student_number = value


class FacultyProfile(Base):
    __tablename__ = "faculty_profiles"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    department_id = Column(BigInteger, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    program_id = Column(BigInteger, ForeignKey("programs.id", ondelete="SET NULL"), nullable=True, index=True)

    user = relationship("User", back_populates="faculty_profile")
    department = relationship("Department")
    program = relationship("Program")

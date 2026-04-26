from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey, Table

from app.models.base import Base

# New normalized table names
event_departments = Table(
    "event_departments",
    Base.metadata,
    Column("event_id", BigInteger, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("department_id", BigInteger, ForeignKey("departments.id", ondelete="CASCADE"), primary_key=True),
    extend_existing=True,
)

event_programs = Table(
    "event_programs",
    Base.metadata,
    Column("event_id", BigInteger, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("program_id", BigInteger, ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True),
    extend_existing=True,
)

program_departments = Table(
    "program_departments",
    Base.metadata,
    Column("program_id", BigInteger, ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True),
    Column("department_id", BigInteger, ForeignKey("departments.id", ondelete="CASCADE"), primary_key=True),
    extend_existing=True,
)

# Compatibility aliases for old import names
event_department_association = event_departments
event_program_association = event_programs
program_department_association = program_departments

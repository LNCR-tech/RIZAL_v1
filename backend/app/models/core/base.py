"""Declarative base for all app models."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

DB_SCHEMA = "public"


class AppBase(DeclarativeBase):
    pass


# Aliases for backward compatibility
Base = AppBase
AURA_NORM_SCHEMA = DB_SCHEMA

__all__ = ["DB_SCHEMA", "AppBase", "Base", "AURA_NORM_SCHEMA"]

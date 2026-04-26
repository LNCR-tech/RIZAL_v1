"""Declarative base for the proposed normalized schema.

These models use a separate SQLAlchemy metadata from `app.models.base.Base` so they
do not affect the current production schema or Alembic autogenerate.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

# Schema is now public — the normalized schema was migrated into public.
AURA_NORM_SCHEMA = "public"


class AuraNormBase(DeclarativeBase):
    pass


# Alias so the rest of the app can import Base from here directly.
Base = AuraNormBase

__all__ = ["AURA_NORM_SCHEMA", "AuraNormBase", "Base"]


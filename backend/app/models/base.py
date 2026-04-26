"""Compatibility shim — re-exports Base from the normalized schema base."""

from app.models.aura_norm.base import AuraNormBase as Base  # noqa: F401

__all__ = ["Base"]

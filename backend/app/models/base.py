"""Re-exports Base from the core model base."""

from app.models.core.base import AppBase as Base  # noqa: F401

__all__ = ["Base"]

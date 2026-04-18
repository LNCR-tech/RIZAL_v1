"""Factory helpers for selecting the active InsightFace engine per route mode."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings

from .insightface_adapter import InsightFaceEngine
from .liveness import LivenessChecker

@lru_cache(maxsize=3)
def _build_engine(mode: str):
    settings = get_settings()
    liveness_checker = LivenessChecker(settings)

    if mode not in {"single", "group", "mfa"}:
        raise ValueError(f"Unsupported face engine mode: {mode}")

    return InsightFaceEngine(settings=settings, liveness_checker=liveness_checker, mode=mode)


def get_engine(mode: str):
    """Return the configured engine instance for one route mode."""
    normalized_mode = mode.strip().lower()
    return _build_engine(normalized_mode)

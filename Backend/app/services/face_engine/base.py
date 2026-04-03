"""Common interfaces and helpers for pluggable face-recognition engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from app.core.config import Settings, get_settings

from .liveness import LivenessChecker


@dataclass(frozen=True)
class FaceCrop:
    """One detected face crop plus the original bounding box."""

    location: tuple[int, int, int, int]
    image_rgb: np.ndarray
    frame_rgb: np.ndarray | None = None
    source: object | None = None


class BaseFaceEngine(ABC):
    """Abstract adapter for one face-recognition runtime."""

    runtime_name = "base"
    embedding_provider = "arcface"

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        liveness_checker: LivenessChecker | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.liveness_checker = liveness_checker or LivenessChecker(self.settings)

    @abstractmethod
    def runtime_status(self) -> tuple[bool, str | None]:
        """Return whether the engine runtime is ready."""

    @abstractmethod
    def detect(self, frame_rgb: np.ndarray) -> list[FaceCrop]:
        """Detect faces and return cropped RGB faces with bounding boxes."""

    @abstractmethod
    def embed(self, face_crop: FaceCrop) -> np.ndarray:
        """Return one canonical ArcFace-compatible embedding."""

    def check_liveness(self, face_crop: FaceCrop) -> float:
        """Return the MiniFASNet real-face score for one crop."""
        return self.liveness_checker.check(
            face_crop.image_rgb,
            frame_rgb=face_crop.frame_rgb,
            location=face_crop.location,
        )

    def normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """L2-normalize one embedding into the canonical dtype."""
        normalized = np.asarray(embedding, dtype=np.float32).reshape(-1)
        if normalized.size != self.settings.face_embedding_dim:
            raise ValueError(
                f"Expected embedding dimension {self.settings.face_embedding_dim}, "
                f"got {normalized.size}."
            )
        norm = float(np.linalg.norm(normalized))
        if norm <= 0:
            raise ValueError("Embedding norm must be greater than zero.")
        return (normalized / norm).astype(np.float32, copy=False)

    def serialize(self, embedding: np.ndarray) -> bytes:
        """Serialize one normalized embedding into raw bytes."""
        return self.normalize_embedding(embedding).tobytes()

"""Use: Contains the main backend rules for face profile, liveness, and recognition rules.
Where to use: Use this from routers, workers, or other services when face profile, liveness, and recognition rules logic is needed.
Role: Service layer. It keeps business logic out of the route files.
"""

from __future__ import annotations

import base64
import hashlib
import io
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings
from app.services.face_engine import FaceCrop, LivenessChecker, get_engine


@dataclass
class LivenessResult:
    """Result of the anti-spoof or liveness check."""

    label: str
    score: float
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "label": self.label,
            "score": round(float(self.score), 6),
        }
        if self.reason:
            payload["reason"] = self.reason
        return payload


@dataclass
class FaceCandidate:
    """One known or registered face that can be matched against."""

    identifier: int | str
    label: str
    encoding_bytes: bytes
    embedding_provider: str | None = None
    embedding_dtype: str | None = None
    embedding_dimension: int | None = None
    embedding_normalized: bool | None = None


@dataclass
class FaceMatchResult:
    """Result of comparing a probe face against one reference or many candidates."""

    matched: bool
    threshold: float
    distance: float
    confidence: float
    candidate: FaceCandidate | None = None


@dataclass
class DetectedFaceProbe:
    """One detected face from a probe image, including liveness and encoding state."""

    index: int
    location: tuple[int, int, int, int]
    liveness: LivenessResult
    encoding: np.ndarray | None = None
    error_code: str | None = None


class FaceRecognitionService:
    """Facade around the configured single, group, and MFA face engines."""

    CANONICAL_PROVIDERS = {"arcface", "buffalo_l"}

    def __init__(self) -> None:
        self.settings = get_settings()
        self.liveness_checker = LivenessChecker(self.settings)
        self._embedding_dtype = np.dtype(self.settings.face_embedding_dtype)

    @staticmethod
    def _fallback_runtime_status(mode: str, *, reason: str) -> dict[str, object]:
        normalized_mode = mode.strip().lower()
        return {
            "state": "failed" if reason == "unsupported_mode" else "initializing",
            "ready": False,
            "reason": reason,
            "last_error": None,
            "provider_target": "CPUExecutionProvider",
            "mode": normalized_mode,
            "initialized_at": None,
            "warmup_started_at": None,
            "warmup_finished_at": None,
            "model_construction_duration_ms": None,
            "prepare_duration_ms": None,
            "warmup_duration_ms": None,
            "init_duration_ms": None,
        }

    def face_runtime_status(self, mode: str = "single") -> dict[str, object]:
        normalized_mode = mode.strip().lower()
        try:
            payload = get_engine(normalized_mode).runtime_status_payload(mode=normalized_mode)
            reason_value = payload.get("reason")
            return {
                "state": str(payload.get("state", "initializing")),
                "ready": bool(payload.get("ready")),
                "reason": (
                    str(reason_value)
                    if reason_value is not None
                    else "insightface_warming_up"
                ),
                "last_error": (
                    str(payload.get("last_error"))
                    if payload.get("last_error") is not None
                    else None
                ),
                "provider_target": str(payload.get("provider_target", "CPUExecutionProvider")),
                "mode": str(payload.get("mode") or normalized_mode),
                "initialized_at": payload.get("initialized_at"),
                "warmup_started_at": payload.get("warmup_started_at"),
                "warmup_finished_at": payload.get("warmup_finished_at"),
                "model_construction_duration_ms": payload.get("model_construction_duration_ms"),
                "prepare_duration_ms": payload.get("prepare_duration_ms"),
                "warmup_duration_ms": payload.get("warmup_duration_ms"),
                "init_duration_ms": payload.get("init_duration_ms"),
            }
        except ValueError:
            return self._fallback_runtime_status(normalized_mode, reason="unsupported_mode")

    def initialize_face_runtime(
        self,
        *,
        mode: str = "single",
        background: bool = True,
        trigger: str = "manual",
        force: bool = False,
    ) -> dict[str, object]:
        normalized_mode = mode.strip().lower()
        try:
            payload = get_engine(normalized_mode).request_runtime_initialization(
                background=background,
                trigger=trigger,
                force=force,
            )
        except ValueError:
            return self._fallback_runtime_status(normalized_mode, reason="unsupported_mode")
        reason_value = payload.get("reason")
        return {
            "state": str(payload.get("state", "initializing")),
            "ready": bool(payload.get("ready")),
            "reason": (
                str(reason_value)
                if reason_value is not None
                else "insightface_warming_up"
            ),
            "last_error": (
                str(payload.get("last_error"))
                if payload.get("last_error") is not None
                else None
            ),
            "provider_target": str(payload.get("provider_target", "CPUExecutionProvider")),
            "mode": str(payload.get("mode") or normalized_mode),
            "initialized_at": payload.get("initialized_at"),
            "warmup_started_at": payload.get("warmup_started_at"),
            "warmup_finished_at": payload.get("warmup_finished_at"),
            "model_construction_duration_ms": payload.get("model_construction_duration_ms"),
            "prepare_duration_ms": payload.get("prepare_duration_ms"),
            "warmup_duration_ms": payload.get("warmup_duration_ms"),
            "init_duration_ms": payload.get("init_duration_ms"),
        }

    @staticmethod
    def decode_base64_image(image_base64: str) -> bytes:
        """Decode a base64 image string into raw bytes."""
        if not image_base64 or not image_base64.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image payload is required.",
            )

        payload = image_base64.strip()
        if "," in payload:
            payload = payload.split(",", 1)[1]

        try:
            return base64.b64decode(payload, validate=True)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image payload is not valid base64.",
            ) from exc

    @staticmethod
    def load_rgb_from_bytes(image_bytes: bytes) -> np.ndarray:
        """Open raw image bytes and convert them into an RGB NumPy array."""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, OSError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid image.",
            ) from exc
        return np.asarray(image, dtype=np.uint8)

    @staticmethod
    def compute_image_sha256(image_bytes: bytes) -> str:
        """Return a SHA-256 fingerprint for an image."""
        return hashlib.sha256(image_bytes).hexdigest()

    def face_recognition_status(self, mode: str = "single") -> tuple[bool, str | None]:
        """Return whether the configured runtime for one mode is available."""
        runtime_status = self.face_runtime_status(mode)
        if runtime_status["ready"]:
            return True, None
        reason = runtime_status.get("reason")
        return False, str(reason) if reason is not None else None

    def ensure_face_runtime_ready(
        self,
        *,
        mode: str = "single",
        context: str | None = None,
    ) -> dict[str, object]:
        runtime_status = self.face_runtime_status(mode)
        if runtime_status["ready"]:
            return runtime_status

        reason = str(runtime_status.get("reason") or "insightface_warming_up")
        state = str(runtime_status.get("state") or "initializing")
        if reason == "unsupported_mode":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "unsupported_face_mode",
                    "message": f"Unsupported face mode: {mode}.",
                    "face_runtime": runtime_status,
                },
            )

        if state == "failed":
            code = "face_runtime_failed"
            message = "Face runtime initialization failed."
        else:
            code = "face_runtime_initializing"
            message = "Face runtime is still initializing."

        detail: dict[str, object] = {
            "code": code,
            "message": message,
            "face_runtime": runtime_status,
        }
        if context:
            detail["context"] = context
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )

    def anti_spoof_status(self) -> tuple[bool, str | None]:
        """Return whether the anti-spoof model is ready."""
        return self.liveness_checker.status()

    def embedding_provider_for_mode(self, mode: str) -> str:
        """Return the canonical embedding provider string stored in the database."""
        _ = get_engine(mode)
        return "arcface"

    def default_threshold_for_mode(self, mode: str) -> float:
        normalized_mode = mode.strip().lower()
        if normalized_mode == "single":
            return float(self.settings.face_threshold_single)
        if normalized_mode == "group":
            return float(self.settings.face_threshold_group)
        if normalized_mode == "mfa":
            return float(self.settings.face_threshold_mfa)
        raise ValueError(f"Unsupported face mode: {mode}")

    def embedding_metadata_for_mode(self, mode: str) -> dict[str, object]:
        """Return the canonical metadata stored with newly enrolled embeddings."""
        return {
            "provider": self.embedding_provider_for_mode(mode),
            "dtype": self.settings.face_embedding_dtype,
            "dimension": self.settings.face_embedding_dim,
            "normalized": True,
        }

    def liveness_passed(self, result: LivenessResult) -> bool:
        """Decide if a liveness result counts as passed."""
        if result.label == "Bypassed":
            return True
        return result.label == "Real" and float(result.score) >= self.settings.liveness_threshold

    def _normalize_embedding(self, encoding: np.ndarray) -> np.ndarray:
        normalized = np.asarray(encoding, dtype=np.float32).reshape(-1)
        if normalized.size != self.settings.face_embedding_dim:
            raise ValueError(
                f"Expected embedding dimension {self.settings.face_embedding_dim}, "
                f"got {normalized.size}."
            )
        norm = float(np.linalg.norm(normalized))
        if norm <= 0:
            raise ValueError("Embedding norm must be greater than zero.")
        return (normalized / norm).astype(np.float32, copy=False)

    def encoding_to_bytes(self, encoding: np.ndarray) -> bytes:
        """Convert one embedding into canonical normalized float32 bytes."""
        return self._normalize_embedding(encoding).astype(self._embedding_dtype, copy=False).tobytes()

    def encoding_from_bytes(
        self,
        encoding_bytes: bytes,
        *,
        dtype: str | None = None,
        dimension: int | None = None,
        normalized: bool = True,
    ) -> np.ndarray:
        """Convert stored raw bytes back into one canonical embedding vector."""
        if not encoding_bytes:
            raise ValueError("Face encoding bytes are empty.")

        dtype_name = (dtype or self.settings.face_embedding_dtype).strip().lower()
        array = np.frombuffer(encoding_bytes, dtype=np.dtype(dtype_name))
        expected_dimension = dimension or self.settings.face_embedding_dim
        if array.size != expected_dimension:
            raise ValueError(
                f"Expected embedding dimension {expected_dimension}, got {array.size}."
            )
        if normalized:
            return self._normalize_embedding(array)
        return np.asarray(array, dtype=np.float32)

    def _evaluate_liveness(self, face_crop: FaceCrop) -> LivenessResult:
        ready, reason = self.anti_spoof_status()
        if not ready and self.settings.allow_liveness_bypass_when_model_missing:
            return LivenessResult(
                label="Bypassed",
                score=1.0,
                reason=reason or "model_unavailable",
            )
        score = self.liveness_checker.check(
            face_crop.image_rgb,
            frame_rgb=face_crop.frame_rgb,
            location=face_crop.location,
        )
        label = "Real" if self.liveness_checker.is_real(score) else "Fake"
        return LivenessResult(label=label, score=score, reason=reason if label == "Bypassed" else None)

    def check_liveness(self, rgb_image: np.ndarray, *, mode: str = "single") -> LivenessResult:
        """Run liveness on one detected face and require exactly one face in frame."""
        self.ensure_face_runtime_ready(mode=mode, context="liveness_check")
        engine = get_engine(mode)
        face_crops = engine.detect(rgb_image)
        if not face_crops:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No face detected for liveness verification.",
            )
        if len(face_crops) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload an image with exactly one face for liveness verification.",
            )
        return self._evaluate_liveness(face_crops[0])

    def analyze_faces_from_bytes(
        self,
        image_bytes: bytes,
        *,
        enforce_liveness: bool = False,
        max_faces: int | None = None,
        mode: str = "single",
    ) -> list[DetectedFaceProbe]:
        """Detect all faces in one probe image and return per-face liveness and embeddings."""
        self.ensure_face_runtime_ready(mode=mode, context="face_analysis")
        engine = get_engine(mode)
        rgb_image = self.load_rgb_from_bytes(image_bytes)
        face_crops = engine.detect(rgb_image)
        if not face_crops:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No face detected in image.",
            )
        if max_faces is not None and len(face_crops) > max_faces:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many faces detected in one frame. Maximum allowed is {max_faces}.",
            )

        probes: list[DetectedFaceProbe] = []
        for index, face_crop in enumerate(face_crops):
            if enforce_liveness:
                liveness = self._evaluate_liveness(face_crop)
            else:
                liveness = LivenessResult(
                    label="Bypassed",
                    score=1.0,
                    reason="not_requested",
                )

            error_code = None
            encoding = None
            if not enforce_liveness or self.liveness_passed(liveness):
                try:
                    encoding = engine.embed(face_crop)
                except ValueError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=str(exc),
                    ) from exc
            else:
                error_code = "spoof_detected"

            probes.append(
                DetectedFaceProbe(
                    index=index,
                    location=face_crop.location,
                    liveness=liveness,
                    encoding=encoding,
                    error_code=error_code,
                )
            )

        return probes

    def extract_encoding_from_bytes(
        self,
        image_bytes: bytes,
        *,
        require_single_face: bool = True,
        enforce_liveness: bool = False,
        mode: str = "single",
    ) -> tuple[np.ndarray, LivenessResult]:
        """Load an image, optionally run liveness, then return one face embedding."""
        probes = self.analyze_faces_from_bytes(
            image_bytes,
            enforce_liveness=enforce_liveness,
            mode=mode,
        )
        if require_single_face and len(probes) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image must contain exactly one face.",
            )

        probe = probes[0]
        if probe.error_code == "spoof_detected":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Spoof detected. label={probe.liveness.label} score={probe.liveness.score:.3f}",
            )
        if probe.encoding is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to compute a face encoding from the image.",
            )
        return np.asarray(probe.encoding, dtype=np.float32), probe.liveness

    def _candidate_is_compatible(self, candidate: FaceCandidate) -> bool:
        provider = (candidate.embedding_provider or "").strip().lower()
        if provider and provider not in self.CANONICAL_PROVIDERS:
            return False

        dtype_name = (candidate.embedding_dtype or "").strip().lower()
        if dtype_name and dtype_name != self.settings.face_embedding_dtype:
            return False

        if (
            candidate.embedding_dimension is not None
            and int(candidate.embedding_dimension) != self.settings.face_embedding_dim
        ):
            return False

        if candidate.embedding_normalized is False:
            return False

        expected_bytes = self.settings.face_embedding_dim * self._embedding_dtype.itemsize
        return len(candidate.encoding_bytes) == expected_bytes

    def compare_encodings(
        self,
        probe_encoding: np.ndarray,
        reference_encoding: np.ndarray,
        *,
        threshold: float | None = None,
        mode: str = "single",
    ) -> FaceMatchResult:
        """Compare two embeddings using cosine distance and return a structured result."""
        probe = self._normalize_embedding(probe_encoding)
        reference = self._normalize_embedding(reference_encoding)
        effective_threshold = float(
            self.default_threshold_for_mode(mode) if threshold is None else threshold
        )
        cosine_similarity = float(np.clip(np.dot(probe, reference), -1.0, 1.0))
        cosine_distance = float(max(0.0, 1.0 - cosine_similarity))

        return FaceMatchResult(
            matched=cosine_distance <= effective_threshold,
            threshold=effective_threshold,
            distance=cosine_distance,
            confidence=cosine_similarity,
        )

    def match(
        self,
        embedding: np.ndarray,
        candidates: Iterable[FaceCandidate],
        *,
        threshold: float | None = None,
        mode: str = "single",
    ) -> FaceMatchResult:
        """Compare one probe against many compatible candidates with batch cosine scoring."""
        probe = self._normalize_embedding(embedding)
        effective_threshold = float(
            self.default_threshold_for_mode(mode) if threshold is None else threshold
        )

        compatible_candidates: list[FaceCandidate] = []
        reference_vectors: list[np.ndarray] = []
        for candidate in candidates:
            if not self._candidate_is_compatible(candidate):
                continue
            try:
                reference_vectors.append(
                    self.encoding_from_bytes(
                        candidate.encoding_bytes,
                        dtype=candidate.embedding_dtype,
                        dimension=candidate.embedding_dimension,
                        normalized=(candidate.embedding_normalized is not False),
                    )
                )
                compatible_candidates.append(candidate)
            except ValueError:
                continue

        if not compatible_candidates:
            return FaceMatchResult(
                matched=False,
                threshold=effective_threshold,
                distance=float("inf"),
                confidence=0.0,
                candidate=None,
            )

        references = np.stack(reference_vectors).astype(np.float32, copy=False)
        similarities = np.clip(references @ probe, -1.0, 1.0)
        distances = np.maximum(0.0, 1.0 - similarities)
        best_index = int(np.argmin(distances))

        return FaceMatchResult(
            matched=float(distances[best_index]) <= effective_threshold,
            threshold=effective_threshold,
            distance=float(distances[best_index]),
            confidence=float(similarities[best_index]),
            candidate=compatible_candidates[best_index],
        )

    def find_best_match(
        self,
        probe_encoding: np.ndarray,
        candidates: Iterable[FaceCandidate],
        *,
        threshold: float | None = None,
        mode: str = "single",
    ) -> FaceMatchResult:
        """Backward-compatible alias for batch cosine matching."""
        return self.match(
            probe_encoding,
            candidates,
            threshold=threshold,
            mode=mode,
        )


def is_face_scan_bypass_enabled_for_email(email: str | None) -> bool:
    """Return True when the email is explicitly allowed to bypass live face matching."""
    settings = get_settings()
    if settings.face_scan_bypass_all:
        return True
    if not email:
        return False
    normalized_email = email.strip().lower()
    return normalized_email in set(settings.face_scan_bypass_emails)


def is_face_scan_bypass_enabled_for_user(user: Any) -> bool:
    """Convenience wrapper for checking bypass rules from a user object."""
    settings = get_settings()
    if settings.face_scan_bypass_all:
        return True
    return is_face_scan_bypass_enabled_for_email(getattr(user, "email", None))

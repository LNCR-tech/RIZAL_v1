from __future__ import annotations

import base64
import hashlib
import io
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import face_recognition
import numpy as np
from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None

try:
    import onnxruntime as ort
except Exception:  # pragma: no cover - optional dependency
    ort = None


@dataclass
class LivenessResult:
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
    identifier: int | str
    label: str
    encoding_bytes: bytes


@dataclass
class FaceMatchResult:
    matched: bool
    threshold: float
    distance: float
    confidence: float
    candidate: FaceCandidate | None = None


class FaceRecognitionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.known_faces: dict[str, np.ndarray] = {}
        self._anti_spoof_session = None
        self._anti_spoof_input_name: str | None = None
        self._anti_spoof_output_name: str | None = None
        self._anti_spoof_input_size: tuple[int, int] | None = None
        self._anti_spoof_initialized = False

    def _default_anti_spoof_model_path(self) -> Path:
        configured = self.settings.anti_spoof_model_path.strip()
        if configured:
            return Path(configured)
        return Path(__file__).resolve().parents[2] / "models" / "MiniFASNetV2.onnx"

    @staticmethod
    def decode_base64_image(image_base64: str) -> bytes:
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
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, OSError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid image.",
            ) from exc
        return np.array(image)

    @staticmethod
    def compute_image_sha256(image_bytes: bytes) -> str:
        return hashlib.sha256(image_bytes).hexdigest()

    @staticmethod
    def encoding_to_bytes(encoding: np.ndarray) -> bytes:
        normalized = np.asarray(encoding, dtype=np.float64)
        return normalized.tobytes()

    @staticmethod
    def encoding_from_bytes(encoding_bytes: bytes) -> np.ndarray:
        if not encoding_bytes:
            raise ValueError("Face encoding bytes are empty.")
        return np.frombuffer(encoding_bytes, dtype=np.float64)

    @staticmethod
    def _softmax(values: np.ndarray) -> np.ndarray:
        exp_values = np.exp(values - np.max(values, axis=1, keepdims=True))
        return exp_values / exp_values.sum(axis=1, keepdims=True)

    @staticmethod
    def _xyxy_to_xywh(x1: int, y1: int, x2: int, y2: int) -> list[int]:
        return [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]

    @staticmethod
    def _crop_face_bgr(
        image_bgr: np.ndarray,
        bbox_xywh: list[int],
        scale: float,
        out_h: int,
        out_w: int,
    ) -> np.ndarray:
        src_h, src_w = image_bgr.shape[:2]
        x, y, box_w, box_h = bbox_xywh
        scale = min((src_h - 1) / max(box_h, 1), (src_w - 1) / max(box_w, 1), scale)
        new_w = box_w * scale
        new_h = box_h * scale
        center_x = x + box_w / 2
        center_y = y + box_h / 2

        left = max(0, int(center_x - new_w / 2))
        top = max(0, int(center_y - new_h / 2))
        right = min(src_w - 1, int(center_x + new_w / 2))
        bottom = min(src_h - 1, int(center_y + new_h / 2))

        cropped = image_bgr[top : bottom + 1, left : right + 1]
        if cropped.size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid face crop for liveness detection.",
            )
        if cv2 is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="opencv-python-headless is required for liveness detection.",
            )
        return cv2.resize(cropped, (out_w, out_h))

    def _init_anti_spoof(self) -> None:
        if self._anti_spoof_initialized:
            return

        self._anti_spoof_initialized = True
        model_path = self._default_anti_spoof_model_path()
        if ort is None or cv2 is None or not model_path.exists():
            return

        providers = ["CPUExecutionProvider"]
        try:
            available = set(ort.get_available_providers())
            if "CUDAExecutionProvider" in available:
                providers.insert(0, "CUDAExecutionProvider")
        except Exception:
            pass

        session = ort.InferenceSession(str(model_path), providers=providers)
        input_meta = session.get_inputs()[0]
        output_meta = session.get_outputs()[0]
        height = int(input_meta.shape[2])
        width = int(input_meta.shape[3])

        self._anti_spoof_session = session
        self._anti_spoof_input_name = input_meta.name
        self._anti_spoof_output_name = output_meta.name
        self._anti_spoof_input_size = (height, width)

    def anti_spoof_status(self) -> tuple[bool, str | None]:
        self._init_anti_spoof()
        if self._anti_spoof_session is not None:
            return True, None

        model_path = self._default_anti_spoof_model_path()
        if ort is None:
            return False, "onnxruntime_unavailable"
        if cv2 is None:
            return False, "opencv_unavailable"
        if not model_path.exists():
            return False, "model_missing"
        return False, "session_unavailable"

    def liveness_passed(self, result: LivenessResult) -> bool:
        if result.label == "Bypassed":
            return True
        return result.label == "Real" and float(result.score) >= self.settings.liveness_min_score

    def check_liveness(self, rgb_image: np.ndarray) -> LivenessResult:
        ready, reason = self.anti_spoof_status()
        if not ready:
            if self.settings.allow_liveness_bypass_when_model_missing:
                return LivenessResult(
                    label="Bypassed",
                    score=1.0,
                    reason=reason or "model_unavailable",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Liveness model is not available."
                    if reason is None
                    else f"Liveness model is not available ({reason})."
                ),
            )

        locations = face_recognition.face_locations(rgb_image)
        if not locations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No face detected for liveness verification.",
            )
        if len(locations) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload an image with exactly one face for liveness verification.",
            )

        top, right, bottom, left = locations[0]
        bbox_xywh = self._xyxy_to_xywh(left, top, right, bottom)
        image_bgr = rgb_image[:, :, ::-1].copy()
        input_height, input_width = self._anti_spoof_input_size or (80, 80)
        face_crop = self._crop_face_bgr(
            image_bgr,
            bbox_xywh,
            self.settings.anti_spoof_scale,
            input_height,
            input_width,
        )

        model_input = face_crop.astype(np.float32)
        model_input = np.transpose(model_input, (2, 0, 1))
        model_input = np.expand_dims(model_input, axis=0)

        logits = self._anti_spoof_session.run(
            [self._anti_spoof_output_name],
            {self._anti_spoof_input_name: model_input},
        )[0]
        probabilities = self._softmax(logits)
        label_index = int(np.argmax(probabilities))
        score = float(probabilities[0, label_index])
        label = "Real" if label_index == 1 else "Fake"
        return LivenessResult(label=label, score=score)

    def extract_encoding_from_bytes(
        self,
        image_bytes: bytes,
        *,
        require_single_face: bool = True,
        enforce_liveness: bool = False,
    ) -> tuple[np.ndarray, LivenessResult]:
        rgb_image = self.load_rgb_from_bytes(image_bytes)
        liveness = self.check_liveness(rgb_image) if enforce_liveness else LivenessResult(
            label="Bypassed",
            score=1.0,
            reason="not_requested",
        )

        if enforce_liveness and not self.liveness_passed(liveness):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Spoof detected. label={liveness.label} score={liveness.score:.3f}",
            )

        face_locations = face_recognition.face_locations(rgb_image)
        if not face_locations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No face detected in image.",
            )
        if require_single_face and len(face_locations) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image must contain exactly one face.",
            )

        encodings = face_recognition.face_encodings(
            rgb_image,
            known_face_locations=face_locations if not require_single_face else [face_locations[0]],
        )
        if not encodings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to compute a face encoding from the image.",
            )

        return np.asarray(encodings[0], dtype=np.float64), liveness

    def compare_encodings(
        self,
        probe_encoding: np.ndarray,
        reference_encoding: np.ndarray,
        *,
        threshold: float | None = None,
    ) -> FaceMatchResult:
        distance = float(np.linalg.norm(probe_encoding - reference_encoding))
        effective_threshold = float(
            self.settings.face_match_threshold if threshold is None else threshold
        )
        confidence = max(0.0, 1.0 - distance)
        return FaceMatchResult(
            matched=distance <= effective_threshold,
            threshold=effective_threshold,
            distance=distance,
            confidence=confidence,
        )

    def find_best_match(
        self,
        probe_encoding: np.ndarray,
        candidates: Iterable[FaceCandidate],
        *,
        threshold: float | None = None,
    ) -> FaceMatchResult:
        best_candidate: FaceCandidate | None = None
        best_distance = float("inf")

        for candidate in candidates:
            reference_encoding = self.encoding_from_bytes(candidate.encoding_bytes)
            distance = float(np.linalg.norm(probe_encoding - reference_encoding))
            if distance < best_distance:
                best_distance = distance
                best_candidate = candidate

        effective_threshold = float(
            self.settings.face_match_threshold if threshold is None else threshold
        )
        if best_candidate is None:
            return FaceMatchResult(
                matched=False,
                threshold=effective_threshold,
                distance=float("inf"),
                confidence=0.0,
                candidate=None,
            )

        return FaceMatchResult(
            matched=best_distance <= effective_threshold,
            threshold=effective_threshold,
            distance=best_distance,
            confidence=max(0.0, 1.0 - best_distance),
            candidate=best_candidate,
        )

    def register_face(self, student_id: str, image_path: str) -> bool:
        try:
            with open(image_path, "rb") as handle:
                encoding, _ = self.extract_encoding_from_bytes(handle.read())
            self.known_faces[student_id] = encoding
            return True
        except Exception:
            return False

    def recognize_face(self, image_path: str) -> Optional[str]:
        try:
            with open(image_path, "rb") as handle:
                encoding, _ = self.extract_encoding_from_bytes(handle.read())
            match = self.find_best_match(
                encoding,
                [
                    FaceCandidate(identifier=student_id, label=student_id, encoding_bytes=self.encoding_to_bytes(value))
                    for student_id, value in self.known_faces.items()
                ],
            )
            if not match.matched or match.candidate is None:
                return None
            return str(match.candidate.identifier)
        except Exception:
            return None

    def save_encodings(self, file_path: str) -> None:
        payload = {
            student_id: self.encoding_to_bytes(encoding)
            for student_id, encoding in self.known_faces.items()
        }
        with open(file_path, "wb") as handle:
            pickle.dump(payload, handle)

    def load_encodings(self, file_path: str) -> None:
        try:
            with open(file_path, "rb") as handle:
                payload = pickle.load(handle)
        except FileNotFoundError:
            self.known_faces = {}
            return

        if not isinstance(payload, dict):
            self.known_faces = {}
            return

        restored: dict[str, np.ndarray] = {}
        for student_id, value in payload.items():
            try:
                if isinstance(value, np.ndarray):
                    restored[str(student_id)] = np.asarray(value, dtype=np.float64)
                elif isinstance(value, (bytes, bytearray)):
                    restored[str(student_id)] = self.encoding_from_bytes(bytes(value))
            except Exception:
                continue
        self.known_faces = restored

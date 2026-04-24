"""MiniFASNet-based anti-spoofing helpers shared by face engines."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None

try:
    import onnxruntime as ort
except Exception:  # pragma: no cover - optional dependency
    ort = None


class LivenessChecker:
    """Evaluate one face crop with the MiniFASNet anti-spoof model."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._session = None
        self._input_name: str | None = None
        self._output_name: str | None = None
        self._input_size: tuple[int, int] | None = None
        self._initialized = False

    def _default_model_path(self) -> Path:
        configured = self.settings.anti_spoof_model_path.strip()
        if configured:
            return Path(configured)
        return Path(__file__).resolve().parents[3] / "models" / "MiniFASNetV2.onnx"

    def _expand_crop_with_context(self, face_crop_rgb: np.ndarray) -> np.ndarray:
        """Fallback context expansion for crops that do not have the original frame."""
        crop = np.asarray(face_crop_rgb)
        if crop.ndim != 3 or crop.shape[2] != 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid face crop for liveness verification.",
            )

        height, width = crop.shape[:2]
        if height <= 0 or width <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid face crop for liveness verification.",
            )

        scale = max(1.0, float(self.settings.anti_spoof_scale))
        target_size = max(height, width, int(round(max(height, width) * scale)))
        pad_y = max(0, target_size - height)
        pad_x = max(0, target_size - width)
        top = pad_y // 2
        bottom = pad_y - top
        left = pad_x // 2
        right = pad_x - left

        return np.pad(
            crop,
            ((top, bottom), (left, right), (0, 0)),
            mode="edge",
        )

    def _crop_from_frame_with_context(
        self,
        frame_rgb: np.ndarray,
        location: tuple[int, int, int, int],
    ) -> np.ndarray:
        """Crop the original frame with the upstream Silent-Face bbox scale logic."""
        frame = np.asarray(frame_rgb)
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid source frame for liveness verification.",
            )

        top, right, bottom, left = [int(value) for value in location]
        src_h, src_w = frame.shape[:2]
        box_w = max(1, right - left)
        box_h = max(1, bottom - top)
        scale = max(1.0, float(self.settings.anti_spoof_scale))
        scale = min((src_h - 1) / box_h, min((src_w - 1) / box_w, scale))

        new_width = box_w * scale
        new_height = box_h * scale
        center_x = box_w / 2.0 + left
        center_y = box_h / 2.0 + top

        left_top_x = center_x - new_width / 2.0
        left_top_y = center_y - new_height / 2.0
        right_bottom_x = center_x + new_width / 2.0
        right_bottom_y = center_y + new_height / 2.0

        if left_top_x < 0:
            right_bottom_x -= left_top_x
            left_top_x = 0
        if left_top_y < 0:
            right_bottom_y -= left_top_y
            left_top_y = 0
        if right_bottom_x > src_w - 1:
            left_top_x -= right_bottom_x - src_w + 1
            right_bottom_x = src_w - 1
        if right_bottom_y > src_h - 1:
            left_top_y -= right_bottom_y - src_h + 1
            right_bottom_y = src_h - 1

        x1 = max(0, int(round(left_top_x)))
        y1 = max(0, int(round(left_top_y)))
        x2 = min(src_w - 1, int(round(right_bottom_x)))
        y2 = min(src_h - 1, int(round(right_bottom_y)))
        if x2 < x1 or y2 < y1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid face crop for liveness verification.",
            )
        return np.asarray(frame[y1 : y2 + 1, x1 : x2 + 1], dtype=np.uint8)

    @staticmethod
    def _softmax(values: np.ndarray) -> np.ndarray:
        exp_values = np.exp(values - np.max(values, axis=1, keepdims=True))
        return exp_values / exp_values.sum(axis=1, keepdims=True)

    def _init_session(self) -> None:
        if self._initialized:
            return

        self._initialized = True
        model_path = self._default_model_path()
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
        self._session = session
        self._input_name = input_meta.name
        self._output_name = output_meta.name
        self._input_size = (int(input_meta.shape[2]), int(input_meta.shape[3]))

    def status(self) -> tuple[bool, str | None]:
        self._init_session()
        if self._session is not None:
            return True, None

        model_path = self._default_model_path()
        if ort is None:
            return False, "onnxruntime_unavailable"
        if cv2 is None:
            return False, "opencv_unavailable"
        if not model_path.exists():
            return False, "model_missing"
        return False, "session_unavailable"

    def is_real(self, score: float) -> bool:
        return float(score) >= self.settings.liveness_threshold

    def check(
        self,
        face_crop_rgb: np.ndarray,
        *,
        frame_rgb: np.ndarray | None = None,
        location: tuple[int, int, int, int] | None = None,
    ) -> float:
        ready, reason = self.status()
        if not ready:
            if self.settings.allow_liveness_bypass_when_model_missing:
                return 1.0
            detail = "Liveness model is not available."
            if reason:
                detail = f"Liveness model is not available ({reason})."
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail,
            )

        if cv2 is None or self._session is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="opencv-python-headless is required for liveness detection.",
            )

        crop = np.asarray(face_crop_rgb)
        if crop.size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid face crop for liveness verification.",
            )
        if frame_rgb is not None and location is not None:
            crop = self._crop_from_frame_with_context(frame_rgb, location)
        else:
            crop = self._expand_crop_with_context(crop)

        input_height, input_width = self._input_size or (80, 80)
        crop_bgr = crop[:, :, ::-1].copy()
        resized = cv2.resize(crop_bgr, (input_width, input_height))
        model_input = resized.astype(np.float32)
        model_input = np.transpose(model_input, (2, 0, 1))
        model_input = np.expand_dims(model_input, axis=0)

        logits = self._session.run(
            [self._output_name],
            {self._input_name: model_input},
        )[0]
        probabilities = self._softmax(logits)
        return float(probabilities[0, 1])

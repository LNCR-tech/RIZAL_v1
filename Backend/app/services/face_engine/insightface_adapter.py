"""InsightFace-backed face engine using SCRFD detection and ArcFace embeddings."""

from __future__ import annotations

import importlib
from pathlib import Path
import threading
from typing import Any

import numpy as np
from fastapi import HTTPException, status

from .base import BaseFaceEngine, FaceCrop


class InsightFaceEngine(BaseFaceEngine):
    """Use InsightFace FaceAnalysis for single, group, and MFA face flows."""

    runtime_name = "insightface"
    embedding_provider = "arcface"
    model_name = "buffalo_l"
    required_model_files = (
        "1k3d68.onnx",
        "2d106det.onnx",
        "det_10g.onnx",
        "genderage.onnx",
        "w600k_r50.onnx",
    )
    _shared_face_analysis: Any = None
    _shared_init_lock = threading.Lock()
    _shared_warming_thread: threading.Thread | None = None
    _shared_runtime_reason: str | None = None

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)

    @staticmethod
    def _load_runtime() -> Any:
        try:
            return importlib.import_module("insightface")
        except Exception as exc:  # pragma: no cover - optional dependency
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "InsightFace runtime is unavailable. Install the 'insightface' "
                    "dependency to use group attendance features."
                ),
            ) from exc

    @classmethod
    def _model_root(cls) -> Path:
        return Path.home() / ".insightface" / "models"

    @classmethod
    def _model_bundle_dir(cls) -> Path:
        return cls._model_root() / cls.model_name

    @classmethod
    def _model_archive_path(cls) -> Path:
        return cls._model_root() / f"{cls.model_name}.zip"

    @classmethod
    def _model_bundle_ready(cls) -> bool:
        bundle_dir = cls._model_bundle_dir()
        if not bundle_dir.is_dir():
            return False
        return all((bundle_dir / filename).is_file() for filename in cls.required_model_files)

    def _initialize_face_analysis(self):
        cls = type(self)
        if cls._shared_face_analysis is not None:
            return cls._shared_face_analysis

        runtime = self._load_runtime()
        try:
            with cls._shared_init_lock:
                if cls._shared_face_analysis is not None:
                    return cls._shared_face_analysis

                face_analysis = runtime.app.FaceAnalysis(
                    name=self.model_name,
                    providers=["CPUExecutionProvider"],
                )
                face_analysis.prepare(ctx_id=-1, det_size=(640, 640))
                cls._shared_face_analysis = face_analysis
                cls._shared_runtime_reason = None
        except Exception as exc:
            cls._shared_runtime_reason = (
                "insightface_initialization_failed"
                if cls._model_bundle_ready()
                else "insightface_model_download_pending"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="InsightFace FaceAnalysis could not be initialized.",
            ) from exc

        return cls._shared_face_analysis

    def _ensure_background_initialization(self) -> None:
        cls = type(self)
        if cls._shared_face_analysis is not None:
            return

        worker = cls._shared_warming_thread
        if worker is not None and worker.is_alive():
            return

        with cls._shared_init_lock:
            if cls._shared_face_analysis is not None:
                return
            worker = cls._shared_warming_thread
            if worker is not None and worker.is_alive():
                return

            cls._shared_runtime_reason = None
            thread: threading.Thread | None = None

            def warm() -> None:
                try:
                    self._initialize_face_analysis()
                except HTTPException:
                    pass
                finally:
                    with cls._shared_init_lock:
                        if cls._shared_warming_thread is thread:
                            cls._shared_warming_thread = None

            thread = threading.Thread(
                target=warm,
                name=f"insightface-warmup-{id(self)}",
                daemon=True,
            )
            cls._shared_warming_thread = thread
            thread.start()

    def _get_face_analysis(self):
        cls = type(self)
        if cls._shared_face_analysis is not None:
            return cls._shared_face_analysis
        return self._initialize_face_analysis()

    def runtime_status(self) -> tuple[bool, str | None]:
        cls = type(self)
        try:
            self._load_runtime()
        except HTTPException:
            return False, "insightface_unavailable"

        if cls._shared_face_analysis is not None:
            return True, None

        bundle_ready = cls._model_bundle_ready()
        self._ensure_background_initialization()

        if cls._shared_face_analysis is not None:
            return True, None
        if cls._shared_runtime_reason is not None:
            return False, cls._shared_runtime_reason
        if bundle_ready:
            return False, "insightface_warming_up"
        if cls._model_archive_path().exists():
            return False, "insightface_model_download_pending"
        return False, "insightface_model_download_pending"

    def detect(self, frame_rgb: np.ndarray) -> list[FaceCrop]:
        face_analysis = self._get_face_analysis()
        frame_uint8 = np.asarray(frame_rgb, dtype=np.uint8)
        try:
            detections = face_analysis.get(frame_uint8)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to detect faces with the InsightFace SCRFD pipeline.",
            ) from exc

        image_height, image_width = frame_uint8.shape[:2]
        crops: list[FaceCrop] = []
        for detection in detections or []:
            bbox = np.asarray(getattr(detection, "bbox", []), dtype=np.float32).reshape(-1)
            if bbox.size < 4:
                continue
            left = max(0, int(bbox[0]))
            top = max(0, int(bbox[1]))
            right = min(image_width, int(bbox[2]))
            bottom = min(image_height, int(bbox[3]))
            if right <= left or bottom <= top:
                continue
            crops.append(
                FaceCrop(
                    location=(top, right, bottom, left),
                    image_rgb=np.asarray(frame_uint8[top:bottom, left:right], dtype=np.uint8),
                    frame_rgb=frame_uint8,
                    source=detection,
                )
            )
        return crops

    def embed(self, face_crop: FaceCrop) -> np.ndarray:
        detection = face_crop.source
        embedding = None
        if detection is not None:
            embedding = getattr(detection, "normed_embedding", None)
            if embedding is None:
                embedding = getattr(detection, "embedding", None)

        if embedding is None:
            face_analysis = self._get_face_analysis()
            try:
                detections = face_analysis.get(face_crop.image_rgb)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to compute an ArcFace embedding with InsightFace.",
                ) from exc
            if detections:
                embedding = getattr(detections[0], "normed_embedding", None) or getattr(
                    detections[0],
                    "embedding",
                    None,
                )

        if embedding is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="InsightFace did not return an embedding for the detected face.",
            )
        return self.normalize_embedding(np.asarray(embedding, dtype=np.float32))

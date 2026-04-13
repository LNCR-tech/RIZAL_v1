"""InsightFace-backed face engine using SCRFD detection and ArcFace embeddings."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
import threading
import time
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
    _model_init_wait_timeout_seconds = 600
    _model_init_wait_poll_seconds = 1.0
    _stale_model_init_lock_seconds = 60

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
    def _model_init_lock_path(cls) -> Path:
        return cls._model_root() / f"{cls.model_name}.init.lock"

    @classmethod
    def _model_bundle_ready(cls) -> bool:
        bundle_dir = cls._model_bundle_dir()
        if not bundle_dir.is_dir():
            return False
        return all((bundle_dir / filename).is_file() for filename in cls.required_model_files)

    @classmethod
    def _acquire_model_init_lock(cls) -> int | None:
        lock_path = cls._model_init_lock_path()
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                try:
                    os.write(lock_fd, str(os.getpid()).encode("ascii"))
                except OSError:
                    pass
                return lock_fd
            except FileExistsError:
                owner_pid: int | None = None
                try:
                    owner_pid = int(lock_path.read_text(encoding="utf-8").strip())
                except Exception:
                    owner_pid = None

                if owner_pid is not None and owner_pid > 0 and cls._pid_exists(owner_pid):
                    return None

                lock_age_seconds = 0.0
                try:
                    lock_age_seconds = time.time() - float(lock_path.stat().st_mtime)
                except OSError:
                    return None

                if lock_age_seconds < float(cls._stale_model_init_lock_seconds):
                    return None

                try:
                    lock_path.unlink()
                except OSError:
                    return None
        return None

    @staticmethod
    def _pid_exists(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    @classmethod
    def _release_model_init_lock(cls, lock_fd: int | None) -> None:
        if lock_fd is None:
            return

        try:
            os.close(lock_fd)
        except OSError:
            pass

        try:
            cls._model_init_lock_path().unlink()
        except FileNotFoundError:
            pass
        except OSError:
            # Another process may already own or have removed the lock file.
            pass

    @classmethod
    def _wait_for_model_bundle_ready(cls) -> bool:
        deadline = time.monotonic() + float(cls._model_init_wait_timeout_seconds)
        while time.monotonic() < deadline:
            if cls._model_bundle_ready():
                return True
            time.sleep(float(cls._model_init_wait_poll_seconds))
        return cls._model_bundle_ready()

    def _initialize_face_analysis(self):
        cls = type(self)
        if cls._shared_face_analysis is not None:
            return cls._shared_face_analysis

        runtime = self._load_runtime()
        model_lock_fd: int | None = None
        try:
            with cls._shared_init_lock:
                if cls._shared_face_analysis is not None:
                    return cls._shared_face_analysis

                model_lock_fd = cls._acquire_model_init_lock()
                if model_lock_fd is None and not cls._model_bundle_ready():
                    # Another process is likely downloading the model bundle.
                    if not cls._wait_for_model_bundle_ready():
                        # One more optimistic lock attempt helps recover from stale lock files.
                        model_lock_fd = cls._acquire_model_init_lock()
                        if model_lock_fd is None and not cls._model_bundle_ready():
                            cls._shared_runtime_reason = "insightface_warming_up"
                            raise HTTPException(
                                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="InsightFace model warm-up is still in progress. Please retry shortly.",
                            )

                face_analysis = runtime.app.FaceAnalysis(
                    name=self.model_name,
                    providers=["CPUExecutionProvider"],
                )
                face_analysis.prepare(ctx_id=-1, det_size=(640, 640))
                cls._shared_face_analysis = face_analysis
                cls._shared_runtime_reason = None
        except HTTPException:
            raise
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
        finally:
            cls._release_model_init_lock(model_lock_fd)

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
        worker = cls._shared_warming_thread
        if worker is not None and worker.is_alive():
            cls._shared_runtime_reason = "insightface_warming_up"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="InsightFace model warm-up is in progress. Please retry shortly.",
            )

        # Start warm-up in the background and fail fast so face routes do not
        # block for several minutes during the first model download.
        self._ensure_background_initialization()
        worker = cls._shared_warming_thread
        if worker is not None and worker.is_alive() and cls._shared_face_analysis is None:
            cls._shared_runtime_reason = (
                cls._shared_runtime_reason or "insightface_model_download_pending"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="InsightFace model warm-up is in progress. Please retry shortly.",
            )

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

"""InsightFace-backed face engine using SCRFD detection and ArcFace embeddings."""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import threading
import time
from typing import Any, Literal

import numpy as np
from fastapi import HTTPException, status

from .base import BaseFaceEngine, FaceCrop

logger = logging.getLogger(__name__)

RuntimeState = Literal["initializing", "ready", "failed"]


@dataclass(frozen=True)
class InsightFaceRuntimeState:
    state: RuntimeState
    reason: str
    initialized_at: datetime | None = None
    last_error: str | None = None
    warmup_started_at: datetime | None = None
    warmup_finished_at: datetime | None = None
    model_construction_duration_ms: float | None = None
    prepare_duration_ms: float | None = None
    warmup_duration_ms: float | None = None
    init_duration_ms: float | None = None


class FaceRuntimeInitializationError(RuntimeError):
    def __init__(self, *, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


class InsightFaceEngine(BaseFaceEngine):
    """Use InsightFace FaceAnalysis for single, group, and MFA face flows."""

    runtime_name = "insightface"
    embedding_provider = "arcface"
    model_name = "buffalo_l"
    provider_target = "CPUExecutionProvider"
    allowed_modules = ("detection", "recognition")
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
    _shared_runtime_state = InsightFaceRuntimeState(
        state="initializing",
        reason="insightface_initialization_not_requested",
    )
    _model_init_wait_timeout_seconds = 600
    _model_init_wait_poll_seconds = 1.0
    _stale_model_init_lock_seconds = 60
    _warmup_image_shape = (640, 640, 3)

    def __init__(self, **kwargs: object) -> None:
        self.mode = (
            str(kwargs.pop("mode", "")).strip().lower() or None
        )
        super().__init__(**kwargs)

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _to_iso8601(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    @staticmethod
    def _elapsed_ms(start_time: float) -> float:
        return round((time.perf_counter() - start_time) * 1000.0, 3)

    def _payload_from_state(
        self,
        *,
        runtime_state: InsightFaceRuntimeState,
        ready: bool,
        mode: str | None = None,
    ) -> dict[str, object]:
        effective_mode = (mode or self.mode or "").strip().lower() or None
        return {
            "state": runtime_state.state,
            "ready": ready,
            "reason": runtime_state.reason,
            "last_error": runtime_state.last_error,
            "provider_target": self.provider_target,
            "mode": effective_mode,
            "initialized_at": self._to_iso8601(runtime_state.initialized_at),
            "warmup_started_at": self._to_iso8601(runtime_state.warmup_started_at),
            "warmup_finished_at": self._to_iso8601(runtime_state.warmup_finished_at),
            "model_construction_duration_ms": runtime_state.model_construction_duration_ms,
            "prepare_duration_ms": runtime_state.prepare_duration_ms,
            "warmup_duration_ms": runtime_state.warmup_duration_ms,
            "init_duration_ms": runtime_state.init_duration_ms,
        }

    @classmethod
    def _set_runtime_state(
        cls,
        *,
        state: RuntimeState,
        reason: str,
        initialized_at: datetime | None,
        last_error: str | None,
        warmup_started_at: datetime | None,
        warmup_finished_at: datetime | None,
        model_construction_duration_ms: float | None = None,
        prepare_duration_ms: float | None = None,
        warmup_duration_ms: float | None = None,
        init_duration_ms: float | None = None,
    ) -> None:
        cls._shared_runtime_state = InsightFaceRuntimeState(
            state=state,
            reason=reason,
            initialized_at=initialized_at,
            last_error=last_error,
            warmup_started_at=warmup_started_at,
            warmup_finished_at=warmup_finished_at,
            model_construction_duration_ms=model_construction_duration_ms,
            prepare_duration_ms=prepare_duration_ms,
            warmup_duration_ms=warmup_duration_ms,
            init_duration_ms=init_duration_ms,
        )

    @classmethod
    def _initializing_reason(cls) -> str:
        return "insightface_warming_up" if cls._model_bundle_ready() else "insightface_model_download_pending"

    @staticmethod
    def _load_runtime() -> Any:
        try:
            return importlib.import_module("insightface")
        except Exception as exc:  # pragma: no cover - optional dependency
            raise FaceRuntimeInitializationError(
                reason="insightface_unavailable",
                message=(
                    "InsightFace runtime is unavailable. Install the 'insightface' "
                    "dependency to use face recognition features."
                ),
            ) from exc

    @classmethod
    def _model_root(cls) -> Path:
        return Path.home() / ".insightface" / "models"

    @classmethod
    def _model_bundle_dir(cls) -> Path:
        return cls._model_root() / cls.model_name

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

    def _run_warmup_inference(self, face_analysis: Any) -> None:
        height, width, channels = self._warmup_image_shape
        dummy_frame = np.zeros((height, width, channels), dtype=np.uint8)
        dummy_frame[:, :, 0] = np.linspace(0, 255, width, dtype=np.uint8)
        dummy_frame[:, :, 1] = np.linspace(255, 0, height, dtype=np.uint8).reshape(height, 1)

        try:
            detections = face_analysis.get(dummy_frame)
            if detections:
                first_detection = detections[0]
                _ = getattr(first_detection, "normed_embedding", None) or getattr(
                    first_detection,
                    "embedding",
                    None,
                )
        except Exception as exc:
            raise FaceRuntimeInitializationError(
                reason="insightface_warmup_failed",
                message=f"InsightFace warm-up inference failed: {exc}",
            ) from exc

    def _build_face_analysis(self, runtime: Any) -> Any:
        kwargs: dict[str, object] = {
            "name": self.model_name,
            "providers": [self.provider_target],
        }
        if self.allowed_modules:
            kwargs["allowed_modules"] = list(self.allowed_modules)

        try:
            return runtime.app.FaceAnalysis(**kwargs)
        except TypeError:
            if "allowed_modules" not in kwargs:
                raise
            logger.warning(
                "Face runtime FaceAnalysis does not support allowed_modules; using default module set."
            )
            kwargs.pop("allowed_modules", None)
            return runtime.app.FaceAnalysis(**kwargs)

    def _initialize_runtime(self, *, trigger: str) -> None:
        cls = type(self)
        with cls._shared_init_lock:
            if cls._shared_face_analysis is not None and cls._shared_runtime_state.state == "ready":
                return

        logger.info(
            "Face runtime init started (runtime=%s, trigger=%s, provider_target=%s, allowed_modules=%s).",
            self.runtime_name,
            trigger,
            self.provider_target,
            ",".join(self.allowed_modules) if self.allowed_modules else "default",
        )

        model_lock_fd: int | None = None
        init_started_perf = time.perf_counter()
        model_construction_duration_ms: float | None = None
        prepare_duration_ms: float | None = None
        warmup_duration_ms: float | None = None
        init_duration_ms: float | None = None
        warmup_started_at: datetime | None = None
        warmup_finished_at: datetime | None = None
        try:
            runtime = self._load_runtime()
            with cls._shared_init_lock:
                current = cls._shared_runtime_state
                cls._set_runtime_state(
                    state="initializing",
                    reason=cls._initializing_reason(),
                    initialized_at=current.initialized_at,
                    last_error=None,
                    warmup_started_at=current.warmup_started_at,
                    warmup_finished_at=None,
                    model_construction_duration_ms=current.model_construction_duration_ms,
                    prepare_duration_ms=current.prepare_duration_ms,
                    warmup_duration_ms=current.warmup_duration_ms,
                    init_duration_ms=current.init_duration_ms,
                )

            model_lock_fd = cls._acquire_model_init_lock()
            if model_lock_fd is None and not cls._model_bundle_ready():
                with cls._shared_init_lock:
                    current = cls._shared_runtime_state
                    cls._set_runtime_state(
                        state="initializing",
                        reason="insightface_model_download_pending",
                        initialized_at=current.initialized_at,
                        last_error=None,
                        warmup_started_at=current.warmup_started_at,
                        warmup_finished_at=None,
                        model_construction_duration_ms=current.model_construction_duration_ms,
                        prepare_duration_ms=current.prepare_duration_ms,
                        warmup_duration_ms=current.warmup_duration_ms,
                        init_duration_ms=current.init_duration_ms,
                    )
                if not cls._wait_for_model_bundle_ready():
                    model_lock_fd = cls._acquire_model_init_lock()
                    if model_lock_fd is None and not cls._model_bundle_ready():
                        raise FaceRuntimeInitializationError(
                            reason="insightface_initialization_failed",
                            message=(
                                "InsightFace model warm-up is still in progress in another worker "
                                "and did not complete before timeout."
                            ),
                        )

            logger.info(
                "Face runtime model construction started (runtime=%s, provider_target=%s, allowed_modules=%s).",
                self.runtime_name,
                self.provider_target,
                ",".join(self.allowed_modules) if self.allowed_modules else "default",
            )
            model_construction_started_perf = time.perf_counter()
            face_analysis = self._build_face_analysis(runtime)
            model_construction_duration_ms = self._elapsed_ms(model_construction_started_perf)
            logger.info(
                "Face runtime model construction completed in %.3f ms.",
                model_construction_duration_ms,
            )

            prepare_started_perf = time.perf_counter()
            face_analysis.prepare(ctx_id=-1, det_size=(640, 640))
            prepare_duration_ms = self._elapsed_ms(prepare_started_perf)
            logger.info("Face runtime prepare completed in %.3f ms.", prepare_duration_ms)

            warmup_started_at = self._now_utc()
            with cls._shared_init_lock:
                current = cls._shared_runtime_state
                cls._set_runtime_state(
                    state="initializing",
                    reason="insightface_warming_up",
                    initialized_at=current.initialized_at,
                    last_error=None,
                    warmup_started_at=warmup_started_at,
                    warmup_finished_at=None,
                    model_construction_duration_ms=model_construction_duration_ms,
                    prepare_duration_ms=prepare_duration_ms,
                    warmup_duration_ms=None,
                    init_duration_ms=None,
                )

            logger.info("Face runtime warm-up started.")
            warmup_started_perf = time.perf_counter()
            try:
                self._run_warmup_inference(face_analysis)
            except FaceRuntimeInitializationError:
                raise
            except Exception as exc:
                raise FaceRuntimeInitializationError(
                    reason="insightface_warmup_failed",
                    message=f"InsightFace warm-up inference failed: {exc}",
                ) from exc
            warmup_duration_ms = self._elapsed_ms(warmup_started_perf)
            warmup_finished_at = self._now_utc()
            logger.info("Face runtime warm-up completed in %.3f ms.", warmup_duration_ms)

            init_duration_ms = self._elapsed_ms(init_started_perf)

            ready_at = self._now_utc()
            with cls._shared_init_lock:
                cls._shared_face_analysis = face_analysis
                cls._set_runtime_state(
                    state="ready",
                    reason="ready",
                    initialized_at=ready_at,
                    last_error=None,
                    warmup_started_at=warmup_started_at,
                    warmup_finished_at=warmup_finished_at or ready_at,
                    model_construction_duration_ms=model_construction_duration_ms,
                    prepare_duration_ms=prepare_duration_ms,
                    warmup_duration_ms=warmup_duration_ms,
                    init_duration_ms=init_duration_ms,
                )
            logger.info(
                "Face runtime ready (runtime=%s, provider_target=%s, init_total_ms=%.3f).",
                self.runtime_name,
                self.provider_target,
                init_duration_ms or 0.0,
            )
        except FaceRuntimeInitializationError as exc:
            failed_at = self._now_utc()
            init_duration_ms = init_duration_ms or self._elapsed_ms(init_started_perf)
            with cls._shared_init_lock:
                current = cls._shared_runtime_state
                cls._shared_face_analysis = None
                cls._set_runtime_state(
                    state="failed",
                    reason=exc.reason,
                    initialized_at=current.initialized_at,
                    last_error=str(exc),
                    warmup_started_at=warmup_started_at or current.warmup_started_at,
                    warmup_finished_at=warmup_finished_at or failed_at,
                    model_construction_duration_ms=(
                        model_construction_duration_ms or current.model_construction_duration_ms
                    ),
                    prepare_duration_ms=prepare_duration_ms or current.prepare_duration_ms,
                    warmup_duration_ms=warmup_duration_ms or current.warmup_duration_ms,
                    init_duration_ms=init_duration_ms,
                )
            logger.exception(
                "Face runtime initialization failed (runtime=%s, reason=%s).",
                self.runtime_name,
                exc.reason,
            )
            raise
        except Exception as exc:
            failed_at = self._now_utc()
            init_duration_ms = init_duration_ms or self._elapsed_ms(init_started_perf)
            with cls._shared_init_lock:
                current = cls._shared_runtime_state
                cls._shared_face_analysis = None
                cls._set_runtime_state(
                    state="failed",
                    reason="insightface_initialization_failed",
                    initialized_at=current.initialized_at,
                    last_error=str(exc),
                    warmup_started_at=warmup_started_at or current.warmup_started_at,
                    warmup_finished_at=warmup_finished_at or failed_at,
                    model_construction_duration_ms=(
                        model_construction_duration_ms or current.model_construction_duration_ms
                    ),
                    prepare_duration_ms=prepare_duration_ms or current.prepare_duration_ms,
                    warmup_duration_ms=warmup_duration_ms or current.warmup_duration_ms,
                    init_duration_ms=init_duration_ms,
                )
            logger.exception(
                "Face runtime initialization failed (runtime=%s, reason=%s).",
                self.runtime_name,
                "insightface_initialization_failed",
            )
            raise
        finally:
            cls._release_model_init_lock(model_lock_fd)

    def _background_initialize_runtime(self, *, trigger: str) -> None:
        cls = type(self)
        try:
            self._initialize_runtime(trigger=trigger)
        except Exception:
            # Status is already tracked in shared runtime state.
            pass
        finally:
            with cls._shared_init_lock:
                if cls._shared_warming_thread is threading.current_thread():
                    cls._shared_warming_thread = None

    def request_runtime_initialization(
        self,
        *,
        background: bool = True,
        trigger: str = "manual",
        force: bool = False,
    ) -> dict[str, object]:
        cls = type(self)
        logger.info(
            "Face runtime init requested (runtime=%s, trigger=%s, background=%s, provider_target=%s).",
            self.runtime_name,
            trigger,
            background,
            self.provider_target,
        )

        thread_to_start: threading.Thread | None = None
        immediate_payload: dict[str, object] | None = None
        with cls._shared_init_lock:
            current = cls._shared_runtime_state
            shared_ready = bool(cls._shared_face_analysis is not None and current.state == "ready")
            if shared_ready:
                immediate_payload = self._payload_from_state(
                    runtime_state=current,
                    ready=True,
                    mode=self.mode,
                )
            elif current.state == "failed" and not force:
                immediate_payload = self._payload_from_state(
                    runtime_state=current,
                    ready=False,
                    mode=self.mode,
                )

            worker = cls._shared_warming_thread if immediate_payload is None else None
            if background and worker is not None and worker.is_alive():
                immediate_payload = self._payload_from_state(
                    runtime_state=current,
                    ready=False,
                    mode=self.mode,
                )

            if immediate_payload is not None:
                return immediate_payload

            now = self._now_utc()
            cls._set_runtime_state(
                state="initializing",
                reason=cls._initializing_reason(),
                initialized_at=current.initialized_at,
                last_error=None,
                warmup_started_at=current.warmup_started_at or now,
                warmup_finished_at=None,
                model_construction_duration_ms=current.model_construction_duration_ms,
                prepare_duration_ms=current.prepare_duration_ms,
                warmup_duration_ms=current.warmup_duration_ms,
                init_duration_ms=current.init_duration_ms,
            )

            if background:
                thread_to_start = threading.Thread(
                    target=self._background_initialize_runtime,
                    kwargs={"trigger": trigger},
                    name=f"insightface-runtime-init-{os.getpid()}",
                    daemon=True,
                )
                cls._shared_warming_thread = thread_to_start

        if thread_to_start is not None:
            thread_to_start.start()
            return self.runtime_status_payload(mode=self.mode)

        self._initialize_runtime(trigger=trigger)
        return self.runtime_status_payload(mode=self.mode)

    def runtime_status_payload(self, *, mode: str | None = None) -> dict[str, object]:
        cls = type(self)

        with cls._shared_init_lock:
            current = cls._shared_runtime_state
            ready = bool(cls._shared_face_analysis is not None and current.state == "ready")
            if cls._shared_face_analysis is not None and current.state != "ready":
                ready_at = current.initialized_at or self._now_utc()
                cls._set_runtime_state(
                    state="ready",
                    reason="ready",
                    initialized_at=ready_at,
                    last_error=None,
                    warmup_started_at=current.warmup_started_at or ready_at,
                    warmup_finished_at=current.warmup_finished_at or ready_at,
                    model_construction_duration_ms=current.model_construction_duration_ms,
                    prepare_duration_ms=current.prepare_duration_ms,
                    warmup_duration_ms=current.warmup_duration_ms,
                    init_duration_ms=current.init_duration_ms,
                )
                current = cls._shared_runtime_state
                ready = True

        return self._payload_from_state(
            runtime_state=current,
            ready=ready,
            mode=mode,
        )

    def _runtime_unavailable_exception(self) -> HTTPException:
        runtime_status = self.runtime_status_payload(mode=self.mode)
        if runtime_status.get("state") == "failed":
            code = "face_runtime_failed"
            message = "Face runtime initialization failed."
        else:
            code = "face_runtime_initializing"
            message = "Face runtime is still initializing."
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": code,
                "message": message,
                "face_runtime": runtime_status,
            },
        )

    def _get_face_analysis(self):
        cls = type(self)
        with cls._shared_init_lock:
            if cls._shared_face_analysis is not None and cls._shared_runtime_state.state == "ready":
                return cls._shared_face_analysis
        raise self._runtime_unavailable_exception()

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

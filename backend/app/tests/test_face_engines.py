from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from app.core.config import get_settings
from app.services.face_engine.factory import _build_engine, get_engine
from app.services.face_engine.insightface_adapter import InsightFaceEngine, InsightFaceRuntimeState
from app.services.face_engine.liveness import LivenessChecker


def _embedding(seed: int) -> np.ndarray:
    vector = np.zeros(512, dtype=np.float32)
    vector[seed % 512] = 0.8
    vector[(seed + 53) % 512] = 0.6
    return vector / np.linalg.norm(vector)


def test_insightface_engine_embed_returns_normalized_float32(monkeypatch) -> None:
    engine = InsightFaceEngine()

    class FakeFace:
        bbox = np.asarray([5, 10, 45, 50], dtype=np.float32)
        normed_embedding = _embedding(27)

    class FakeFaceAnalysis:
        def get(self, _frame):
            return [FakeFace()]

    monkeypatch.setattr(engine, "_get_face_analysis", lambda: FakeFaceAnalysis())

    crop = engine.detect(np.ones((100, 100, 3), dtype=np.uint8))[0]
    embedding = engine.embed(crop)

    assert embedding.dtype == np.float32
    assert embedding.shape == (512,)
    assert np.isclose(np.linalg.norm(embedding), 1.0)


def test_liveness_checker_returns_probability_score() -> None:
    checker = LivenessChecker()

    class FakeSession:
        def run(self, _outputs, _inputs):
            return [np.asarray([[0.2, 2.3]], dtype=np.float32)]

    checker._initialized = True
    checker._session = FakeSession()
    checker._input_name = "input"
    checker._output_name = "output"
    checker._input_size = (80, 80)

    score = checker.check(np.ones((32, 32, 3), dtype=np.uint8))

    assert 0.0 <= score <= 1.0
    assert checker.is_real(score) is True


def test_liveness_checker_applies_configured_context_scale() -> None:
    checker = LivenessChecker(settings=replace(get_settings(), anti_spoof_scale=2.7))

    expanded = checker._expand_crop_with_context(np.ones((40, 20, 3), dtype=np.uint8))

    assert expanded.shape[0] == expanded.shape[1]
    assert expanded.shape[0] >= 108


def test_liveness_checker_uses_original_frame_context_when_available() -> None:
    checker = LivenessChecker()

    class FakeSession:
        def __init__(self) -> None:
            self.last_input = None

        def run(self, _outputs, inputs):
            self.last_input = inputs["input"]
            return [np.asarray([[0.1, 0.9]], dtype=np.float32)]

    session = FakeSession()
    checker._initialized = True
    checker._session = session
    checker._input_name = "input"
    checker._output_name = "output"
    checker._input_size = (80, 80)

    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[40:60, 40:60] = 255
    crop = np.full((20, 20, 3), 255, dtype=np.uint8)

    checker.check(crop, frame_rgb=frame, location=(40, 60, 60, 40))

    assert session.last_input is not None
    assert float(session.last_input.min()) < float(session.last_input.max())


def test_face_engine_factory_returns_expected_engine_per_mode() -> None:
    _build_engine.cache_clear()

    assert isinstance(get_engine("single"), InsightFaceEngine)
    assert isinstance(get_engine("group"), InsightFaceEngine)
    assert isinstance(get_engine("mfa"), InsightFaceEngine)


def test_insightface_runtime_status_reports_model_download_pending(monkeypatch) -> None:
    engine = InsightFaceEngine()

    monkeypatch.setattr(InsightFaceEngine, "_shared_face_analysis", None)
    monkeypatch.setattr(
        InsightFaceEngine,
        "_shared_runtime_state",
        InsightFaceRuntimeState(
            state="initializing",
            reason="insightface_model_download_pending",
        ),
    )

    assert engine.runtime_status() == (False, "insightface_model_download_pending")
    payload = engine.runtime_status_payload(mode="single")
    assert payload["state"] == "initializing"
    assert payload["ready"] is False
    assert payload["mode"] == "single"


def test_insightface_runtime_status_reports_warming_up_with_local_models(monkeypatch) -> None:
    engine = InsightFaceEngine()

    monkeypatch.setattr(InsightFaceEngine, "_shared_face_analysis", None)
    monkeypatch.setattr(
        InsightFaceEngine,
        "_shared_runtime_state",
        InsightFaceRuntimeState(
            state="initializing",
            reason="insightface_warming_up",
        ),
    )

    assert engine.runtime_status() == (False, "insightface_warming_up")


def test_request_runtime_initialization_does_not_spawn_duplicate_worker(monkeypatch) -> None:
    engine = InsightFaceEngine()

    class BusyThread:
        @staticmethod
        def is_alive() -> bool:
            return True

    monkeypatch.setattr(InsightFaceEngine, "_shared_face_analysis", None)
    monkeypatch.setattr(InsightFaceEngine, "_shared_warming_thread", BusyThread())
    monkeypatch.setattr(
        InsightFaceEngine,
        "_shared_runtime_state",
        InsightFaceRuntimeState(
            state="initializing",
            reason="insightface_warming_up",
        ),
    )

    payload = engine.request_runtime_initialization(background=True, trigger="test")
    assert payload["state"] == "initializing"
    assert payload["reason"] == "insightface_warming_up"


def test_initialize_runtime_reports_ready_after_warmup(monkeypatch) -> None:
    engine = InsightFaceEngine()

    class FakeFaceAnalysis:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def prepare(self, *args, **kwargs) -> None:
            return None

    class FakeRuntime:
        class app:
            FaceAnalysis = FakeFaceAnalysis

    monkeypatch.setattr(InsightFaceEngine, "_shared_face_analysis", None)
    monkeypatch.setattr(InsightFaceEngine, "_shared_warming_thread", None)
    monkeypatch.setattr(
        InsightFaceEngine,
        "_shared_runtime_state",
        InsightFaceRuntimeState(
            state="initializing",
            reason="insightface_initialization_not_requested",
        ),
    )
    monkeypatch.setattr(engine, "_load_runtime", lambda: FakeRuntime())
    monkeypatch.setattr(InsightFaceEngine, "_model_bundle_ready", classmethod(lambda cls: True))
    monkeypatch.setattr(InsightFaceEngine, "_acquire_model_init_lock", classmethod(lambda cls: 1))
    monkeypatch.setattr(InsightFaceEngine, "_release_model_init_lock", classmethod(lambda cls, lock_fd: None))
    monkeypatch.setattr(engine, "_run_warmup_inference", lambda _face_analysis: None)

    payload = engine.request_runtime_initialization(background=False, trigger="test", force=True)

    assert payload["state"] == "ready"
    assert payload["ready"] is True
    assert payload["reason"] == "ready"
    assert payload["warmup_started_at"] is not None
    assert payload["warmup_finished_at"] is not None
    assert payload["model_construction_duration_ms"] is not None
    assert payload["prepare_duration_ms"] is not None
    assert payload["warmup_duration_ms"] is not None
    assert payload["init_duration_ms"] is not None


def test_initialize_runtime_marks_failed_when_warmup_fails(monkeypatch) -> None:
    engine = InsightFaceEngine()

    class FakeFaceAnalysis:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def prepare(self, *args, **kwargs) -> None:
            return None

    class FakeRuntime:
        class app:
            FaceAnalysis = FakeFaceAnalysis

    monkeypatch.setattr(InsightFaceEngine, "_shared_face_analysis", None)
    monkeypatch.setattr(InsightFaceEngine, "_shared_warming_thread", None)
    monkeypatch.setattr(
        InsightFaceEngine,
        "_shared_runtime_state",
        InsightFaceRuntimeState(
            state="initializing",
            reason="insightface_initialization_not_requested",
        ),
    )
    monkeypatch.setattr(engine, "_load_runtime", lambda: FakeRuntime())
    monkeypatch.setattr(InsightFaceEngine, "_model_bundle_ready", classmethod(lambda cls: True))
    monkeypatch.setattr(InsightFaceEngine, "_acquire_model_init_lock", classmethod(lambda cls: 1))
    monkeypatch.setattr(InsightFaceEngine, "_release_model_init_lock", classmethod(lambda cls, lock_fd: None))
    monkeypatch.setattr(
        engine,
        "_run_warmup_inference",
        lambda _face_analysis: (_ for _ in ()).throw(RuntimeError("warmup exploded")),
    )

    with pytest.raises(Exception):
        engine.request_runtime_initialization(background=False, trigger="test", force=True)

    payload = engine.runtime_status_payload(mode="single")
    assert payload["state"] == "failed"
    assert payload["ready"] is False
    assert payload["reason"] == "insightface_warmup_failed"
    assert payload["last_error"] is not None

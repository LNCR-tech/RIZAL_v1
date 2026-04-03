from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np

from app.core.config import get_settings
from app.services.face_engine.factory import _build_engine, get_engine
from app.services.face_engine.insightface_adapter import InsightFaceEngine
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


def test_insightface_runtime_status_reports_model_download_pending(monkeypatch, tmp_path) -> None:
    engine = InsightFaceEngine()

    monkeypatch.setattr(InsightFaceEngine, "_shared_face_analysis", None)
    monkeypatch.setattr(InsightFaceEngine, "_shared_runtime_reason", None)
    monkeypatch.setattr(InsightFaceEngine, "_shared_warming_thread", None)
    monkeypatch.setattr(engine, "_load_runtime", lambda: object())
    monkeypatch.setattr(engine, "_ensure_background_initialization", lambda: None)
    monkeypatch.setattr(InsightFaceEngine, "_model_bundle_ready", classmethod(lambda cls: False))
    monkeypatch.setattr(
        InsightFaceEngine,
        "_model_archive_path",
        classmethod(lambda cls: Path(tmp_path / "buffalo_l.zip")),
    )
    (tmp_path / "buffalo_l.zip").write_bytes(b"pending")

    assert engine.runtime_status() == (False, "insightface_model_download_pending")


def test_insightface_runtime_status_reports_warming_up_with_local_models(monkeypatch) -> None:
    engine = InsightFaceEngine()

    monkeypatch.setattr(InsightFaceEngine, "_shared_face_analysis", None)
    monkeypatch.setattr(InsightFaceEngine, "_shared_runtime_reason", None)
    monkeypatch.setattr(InsightFaceEngine, "_shared_warming_thread", None)
    monkeypatch.setattr(engine, "_load_runtime", lambda: object())
    monkeypatch.setattr(engine, "_ensure_background_initialization", lambda: None)
    monkeypatch.setattr(InsightFaceEngine, "_model_bundle_ready", classmethod(lambda cls: True))

    assert engine.runtime_status() == (False, "insightface_warming_up")


def test_background_initialization_returns_immediately_when_worker_is_alive(monkeypatch) -> None:
    engine = InsightFaceEngine()

    class BusyThread:
        @staticmethod
        def is_alive() -> bool:
            return True

    class ExplodingLock:
        def __enter__(self):
            raise AssertionError("status checks should not wait on the warmup lock")

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(InsightFaceEngine, "_shared_face_analysis", None)
    monkeypatch.setattr(InsightFaceEngine, "_shared_warming_thread", BusyThread())
    monkeypatch.setattr(InsightFaceEngine, "_shared_init_lock", ExplodingLock())

    engine._ensure_background_initialization()

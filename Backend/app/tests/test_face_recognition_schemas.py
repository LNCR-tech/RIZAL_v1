from __future__ import annotations

import numpy as np

from app.schemas.face_recognition import FaceRegistrationResponse
from app.services.face_recognition import FaceRecognitionService


def _embedding(seed: int) -> np.ndarray:
    vector = np.zeros(512, dtype=np.float32)
    vector[seed % 512] = 0.8
    vector[(seed + 97) % 512] = 0.6
    return vector / np.linalg.norm(vector)


def test_face_registration_response_allows_missing_student_id() -> None:
    response = FaceRegistrationResponse(
        message="Face registered successfully.",
        student_id=None,
        liveness={"label": "Bypassed", "score": 1.0},
    )

    assert response.student_id is None


def test_encoding_round_trip_uses_canonical_float32_arcface() -> None:
    service = FaceRecognitionService()
    original = _embedding(11)

    encoded = service.encoding_to_bytes(original)
    restored = service.encoding_from_bytes(
        encoded,
        dtype="float32",
        dimension=512,
        normalized=True,
    )

    assert len(encoded) == 2048
    assert restored.dtype == np.float32
    assert restored.shape == (512,)
    assert np.isclose(np.linalg.norm(restored), 1.0)
    assert np.allclose(restored, original, atol=1e-6)


def test_compare_encodings_uses_cosine_distance() -> None:
    service = FaceRecognitionService()
    same = _embedding(21)
    different = _embedding(201)

    same_result = service.compare_encodings(same, same, mode="single")
    different_result = service.compare_encodings(same, different, mode="single")

    assert same_result.matched is True
    assert np.isclose(same_result.distance, 0.0)
    assert np.isclose(same_result.confidence, 1.0)
    assert different_result.matched is False
    assert different_result.distance > same_result.threshold


def test_thresholds_are_mode_specific() -> None:
    service = FaceRecognitionService()

    assert service.default_threshold_for_mode("single") == 0.40
    assert service.default_threshold_for_mode("group") == 0.40
    assert service.default_threshold_for_mode("mfa") == 0.35

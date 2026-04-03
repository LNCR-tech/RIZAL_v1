"""Face engine adapters and helpers for canonical ArcFace embeddings."""

from app.services.face_engine.base import BaseFaceEngine, FaceCrop
from app.services.face_engine.factory import get_engine
from app.services.face_engine.insightface_adapter import InsightFaceEngine
from app.services.face_engine.liveness import LivenessChecker
from app.services.face_engine.vector_store import FAISSVectorStore

__all__ = [
    "BaseFaceEngine",
    "FAISSVectorStore",
    "FaceCrop",
    "InsightFaceEngine",
    "LivenessChecker",
    "get_engine",
]

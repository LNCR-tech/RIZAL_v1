"""Optional FAISS-backed vector search helpers for face embeddings."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Iterable

import numpy as np


class FAISSVectorStore:
    """Build and query a cosine-similarity vector index with numpy fallback."""

    def __init__(self) -> None:
        self._index = None
        self._student_ids: list[object] = []
        self._embeddings: np.ndarray | None = None

    @staticmethod
    def _load_faiss():
        return importlib.import_module("faiss")

    @staticmethod
    def _normalize(embeddings: np.ndarray) -> np.ndarray:
        array = np.asarray(embeddings, dtype=np.float32)
        if array.ndim == 1:
            array = np.expand_dims(array, axis=0)
        norms = np.linalg.norm(array, axis=1, keepdims=True)
        norms = np.where(norms <= 0, 1.0, norms)
        return array / norms

    def build_index(self, embeddings: np.ndarray, student_ids: Iterable[object] | None = None):
        normalized = self._normalize(embeddings)
        self._student_ids = list(student_ids or range(normalized.shape[0]))
        self._embeddings = normalized

        try:
            faiss = self._load_faiss()
            index = faiss.IndexFlatIP(normalized.shape[1])
            index.add(normalized.astype(np.float32))
            self._index = index
        except Exception:
            self._index = None

        return self._index

    def search(self, query: np.ndarray, top_k: int = 5) -> list[tuple[object, float]]:
        if self._embeddings is None or not self._student_ids:
            return []

        normalized_query = self._normalize(query)[0]
        top_k = max(1, min(int(top_k), len(self._student_ids)))

        if self._index is not None:
            scores, indices = self._index.search(np.expand_dims(normalized_query, axis=0), top_k)
            return [
                (self._student_ids[index], float(score))
                for score, index in zip(scores[0], indices[0], strict=False)
                if 0 <= index < len(self._student_ids)
            ]

        scores = self._embeddings @ normalized_query
        best_indices = np.argsort(scores)[::-1][:top_k]
        return [
            (self._student_ids[index], float(scores[index]))
            for index in best_indices
        ]

    def save(self, path: str | Path) -> None:
        if self._index is None:
            return
        faiss = self._load_faiss()
        faiss.write_index(self._index, str(path))

    def load(self, path: str | Path, student_ids: Iterable[object]) -> None:
        faiss = self._load_faiss()
        self._index = faiss.read_index(str(path))
        self._student_ids = list(student_ids)
        self._embeddings = None

"""Offline TF-IDF embedding implementation."""

from __future__ import annotations

import logging

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from interfaces.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

DEFAULT_VECTOR_DIMENSION = 100

DEFAULT_FIT_CORPUS: tuple[str, ...] = (
    "python programming software development",
    "java backend api rest database sql",
    "javascript typescript react frontend web",
    "machine learning data science statistics",
    "devops cloud docker kubernetes ci cd",
    "cybersecurity networking linux security",
    "fastapi flask django sqlalchemy postgresql",
    "algorithms data structures computer science",
    "mobile android ios swift kotlin",
    "project management agile scrum teamwork",
)


class LocalEmbeddingServiceImpl(EmbeddingService):
    def __init__(
        self,
        dimension: int = DEFAULT_VECTOR_DIMENSION,
        fit_corpus: tuple[str, ...] = DEFAULT_FIT_CORPUS,
    ) -> None:
        self._dimension = dimension
        self._fit_corpus = fit_corpus
        self._vectorizer = TfidfVectorizer(
            max_features=dimension,
            stop_words="english",
            lowercase=True,
            norm="l2",
        )
        self._fitted = False

    def get_embedding(self, text: str) -> list[float]:
        if not text or not text.strip():
            return self._fallback_embedding(text or "empty")

        try:
            stripped = text.strip()
            self._ensure_fitted(stripped)
            dense = self._vectorizer.transform([stripped]).toarray()[0]

            if not np.any(dense):
                corpus = list(self._fit_corpus) + [stripped]
                self._vectorizer.fit(corpus)
                self._fitted = True
                dense = self._vectorizer.transform([stripped]).toarray()[0]

            if not np.any(dense):
                return self._fallback_embedding(stripped)

            return self._to_fixed_dimension(dense)
        except Exception:
            logger.exception("get_embedding failed; returning fallback embedding")
            return self._fallback_embedding(text)

    def calculate_similarity(
        self, vector_a: list[float], vector_b: list[float]
    ) -> float:
        if not vector_a or not vector_b:
            return 0.0

        try:
            a = self._align_vector(vector_a)
            b = self._align_vector(vector_b)
            if np.allclose(a, 0.0) or np.allclose(b, 0.0):
                return 0.0

            score = float(
                cosine_similarity(a.reshape(1, -1), b.reshape(1, -1))[0, 0]
            )
            return max(0.0, min(1.0, score))
        except Exception:
            logger.exception("calculate_similarity failed; returning 0.0")
            return 0.0

    def _ensure_fitted(self, text: str) -> None:
        if self._fitted:
            return
        corpus = list(self._fit_corpus)
        stripped = text.strip()
        if stripped and stripped not in corpus:
            corpus.append(stripped)
        self._vectorizer.fit(corpus)
        self._fitted = True

    def _zero_vector(self) -> list[float]:
        return [0.0] * self._dimension

    def _fallback_embedding(self, text: str) -> list[float]:
        seed = sum(ord(char) for char in text.strip().lower()) or 1
        rng = np.random.default_rng(seed)
        vector = rng.standard_normal(self._dimension)
        norm = np.linalg.norm(vector)
        if norm == 0.0:
            return self._zero_vector()
        return (vector / norm).tolist()

    def _to_fixed_dimension(self, vector: np.ndarray) -> list[float]:
        result = self._zero_vector()
        length = min(len(vector), self._dimension)
        if length:
            result[:length] = vector[:length].tolist()
        return result

    def _align_vector(self, vector: list[float]) -> np.ndarray:
        aligned = np.zeros(self._dimension, dtype=np.float64)
        length = min(len(vector), self._dimension)
        if length:
            aligned[:length] = vector[:length]
        return aligned

from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    """Contract for text vectorization and vector similarity scoring."""

    @abstractmethod
    def get_embedding(self, text: str) -> list[float]:
        """Convert text into a fixed-length embedding vector."""

    @abstractmethod
    def calculate_similarity(
        self, vector_a: list[float], vector_b: list[float]
    ) -> float:
        """Return cosine similarity in the range [0.0, 1.0]."""

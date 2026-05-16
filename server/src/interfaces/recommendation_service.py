from abc import ABC, abstractmethod
from typing import List

from dtos import RecommendationResponse


class RecommendationService(ABC):
    """Application service contract for course recommendations."""

    @abstractmethod
    def get_recommendations(self, student_id: int) -> List[RecommendationResponse]:
        ...

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class RecommendationService(ABC):
    """Application service contract for course recommendations."""

    @abstractmethod
    async def get_personalized_recommendations(
        self, db_session: Session, student_id: int
    ) -> list[dict]:
        ...

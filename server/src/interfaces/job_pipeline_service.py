from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class JobPipelineService(ABC):
    """Contract for the industry_jobs Adzuna pipeline."""

    @abstractmethod
    async def sync_from_adzuna(self, db_session: Session, role_title: str) -> int:
        """Fetch from Adzuna and upsert into industry_jobs."""

    @abstractmethod
    def extract_skills_from_listings(self, db_session: Session) -> int:
        """Fill industry_jobs.extracted_skills from descriptions."""

    @abstractmethod
    def vectorize_listings(self, db_session: Session) -> int:
        """Fill industry_jobs.feature_vector from extracted_skills."""

    @abstractmethod
    def get_average_feature_vector(self, db_session: Session) -> dict:
        """Return the mean feature_vector across all vectorized industry_jobs."""

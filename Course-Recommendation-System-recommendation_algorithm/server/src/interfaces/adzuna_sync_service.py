from abc import ABC, abstractmethod
from typing import Any, Optional


class AdzunaSyncService(ABC):
    """Contract for live Adzuna job search API access."""

    @abstractmethod
    async def fetch_search_results(
        self, keyword: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Return raw job result objects from the Adzuna API."""

    @abstractmethod
    async def sync_jobs(self, keyword: Optional[str] = None) -> int:
        """Upsert search results into industry_jobs (requires repository)."""

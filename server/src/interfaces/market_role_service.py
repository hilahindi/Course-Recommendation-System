from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session


class MarketRoleService(ABC):
    """Application service contract for market / job role operations."""

    @abstractmethod
    def sync_job_roles(self, db: Session) -> dict[str, Any]:
        ...

    @abstractmethod
    def ensure_market_roles_in_db(self, db: Session, existing_count: int) -> bool:
        ...

"""Market roles sync: Anthropic API with local mock fallback for development."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from sqlalchemy.orm import Session

import models
from interfaces.market_role_service import MarketRoleService
from repositories.course_repository import CourseRepository

logger = logging.getLogger(__name__)

ANTHROPIC_PLACEHOLDER_VALUES = frozenset(
    {
        "",
        "demo_api_key",
    }
)

MOCK_MARKET_ROLES: list[dict[str, str]] = [
    {"title": "Full-Stack Developer", "demand_level": "High"},
    {"title": "Backend Engineer", "demand_level": "High"},
    {"title": "Frontend Engineer", "demand_level": "High"},
    {"title": "Data Scientist", "demand_level": "High"},
    {"title": "DevOps Engineer", "demand_level": "High"},
    {"title": "Cyber Security Analyst", "demand_level": "High"},
    {"title": "Software Engineer", "demand_level": "High"},
    {"title": "Cloud Engineer", "demand_level": "High"},
    {"title": "Machine Learning Engineer", "demand_level": "High"},
    {"title": "Mobile Developer", "demand_level": "Medium"},
    {"title": "QA Automation Engineer", "demand_level": "Medium"},
    {"title": "Systems Analyst", "demand_level": "Medium"},
]

MOCK_FALLBACK_WARNING = (
    "[Market Roles] Anthropic API key placeholder detected. "
    "Falling back to local mock roles."
)


class MarketRoleServiceImpl(MarketRoleService):
    def __init__(self, repository: CourseRepository):
        self._repository = repository

    @staticmethod
    def is_anthropic_api_configured() -> bool:
        key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
        if not key:
            return False
        if key.lower() in ANTHROPIC_PLACEHOLDER_VALUES:
            return False
        return True

    @staticmethod
    def get_mock_market_roles() -> list[dict[str, str]]:
        return [role.copy() for role in MOCK_MARKET_ROLES]

    def _persist_roles(
        self, db: Session, roles: list[dict[str, str]], *, replace_existing: bool
    ) -> int:
        if replace_existing:
            try:
                db.query(models.JobRole).delete()
                db.commit()
            except Exception:
                db.rollback()
                logger.warning(
                    "[Market Roles] Could not delete existing roles; updating in place."
                )

        added_count = 0
        for role_data in roles:
            title = role_data.get("title")
            if not title:
                continue
            demand = role_data.get("demand_level", "High")
            existing = (
                db.query(models.JobRole).filter(models.JobRole.title == title).first()
            )
            if not existing:
                db.add(models.JobRole(title=title, demand_level=demand))
                added_count += 1

        db.commit()
        return added_count

    def _sync_with_mock(self, db: Session, *, replace_existing: bool = True) -> dict[str, Any]:
        print(MOCK_FALLBACK_WARNING)
        logger.warning(MOCK_FALLBACK_WARNING)
        roles = self.get_mock_market_roles()
        added_count = self._persist_roles(db, roles, replace_existing=replace_existing)
        return {
            "message": "Market roles synchronized from local mock data",
            "source": "mock",
            "added_new_roles": added_count,
            "roles": roles,
        }

    def _sync_with_anthropic(self, db: Session) -> dict[str, Any]:
        import anthropic

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = """
        אתה מומחה קריירה וגיוס טכנולוגי בכיר בישראל. 
        מצא את 8 תפקידי הג'וניור (Entry Level) המבוקשים ביותר כרגע לבוגרי מדעי המחשב.
        החזר רשימת JSON נקייה ללא טקסט נוסף במבנה: 
        [{"title": "שם התפקיד בעברית", "demand_level": "High"}]
        """

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        roles = json.loads(clean_json)

        added_count = self._persist_roles(db, roles, replace_existing=True)
        return {
            "message": "Market roles synchronized successfully",
            "source": "anthropic",
            "added_new_roles": added_count,
            "roles": roles,
        }

    def sync_job_roles(self, db: Session) -> dict[str, Any]:
        if not self.is_anthropic_api_configured():
            return self._sync_with_mock(db, replace_existing=True)

        try:
            return self._sync_with_anthropic(db)
        except Exception as exc:
            logger.exception("[Market Roles] Anthropic sync failed: %s", exc)
            print(
                f"[Market Roles] Anthropic sync failed ({exc}). Falling back to mock roles."
            )
            return self._sync_with_mock(db, replace_existing=True)

    def ensure_market_roles_in_db(self, db: Session, existing_count: int) -> bool:
        """Populate job roles when empty so onboarding always has choices."""
        if existing_count > 0:
            return False

        if self.is_anthropic_api_configured():
            try:
                self._sync_with_anthropic(db)
                return True
            except Exception as exc:
                logger.warning(
                    "[Market Roles] Auto-sync via Anthropic failed (%s); using mock.",
                    exc,
                )

        self._sync_with_mock(db, replace_existing=False)
        return True

"""Live Adzuna job search API client implementation."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

import config  # noqa: F401 — loads server/.env before getenv
from interfaces.adzuna_sync_service import AdzunaSyncService
from repositories.course_repository import CourseRepository

_UNSUPPORTED_COUNTRIES = frozenset({"il", "israel"})
_DEFAULT_APP_ID = "2de5fbaf"
_DEFAULT_APP_KEY = "b5c350f30ceedf1b8608ebe0001f31b9"
_DEFAULT_COUNTRY = "gb"
_DEFAULT_SEARCH_WHAT = "developer"


class AdzunaSyncServiceImpl(AdzunaSyncService):
    RESULTS_PER_PAGE = 50

    def __init__(self, repository: CourseRepository | None = None) -> None:
        self._repository = repository
        self.app_id = os.getenv("ADZUNA_APP_ID", _DEFAULT_APP_ID).strip()
        self.app_key = os.getenv("ADZUNA_APP_KEY", _DEFAULT_APP_KEY).strip()
        self.country_code = self._resolve_country_code()
        self.where = os.getenv("ADZUNA_WHERE", "").strip() or None

    @staticmethod
    def resolve_search_what(keyword: Optional[str]) -> str:
        if keyword is not None and keyword.strip():
            return keyword.strip()
        return (
            os.getenv("ADZUNA_SEARCH_WHAT", _DEFAULT_SEARCH_WHAT).strip()
            or _DEFAULT_SEARCH_WHAT
        )

    @staticmethod
    def _resolve_country_code() -> str:
        country = (
            os.getenv("ADZUNA_COUNTRY", "").strip()
            or os.getenv("ADZUNA_COUNTRY_CODE", _DEFAULT_COUNTRY).strip()
            or _DEFAULT_COUNTRY
        ).lower()
        if country in _UNSUPPORTED_COUNTRIES:
            raise ValueError(
                "Adzuna does not support country code 'il'. Set ADZUNA_COUNTRY=gb."
            )
        return country

    @staticmethod
    def map_industry_job(result: dict) -> dict | None:
        job_id = result.get("id")
        title = result.get("title")
        if job_id is None or not title:
            return None

        description = result.get("description")
        return {
            "id": str(job_id),
            "title": str(title).strip(),
            "description": "" if description is None else str(description),
        }

    async def fetch_search_results(
        self, keyword: Optional[str] = None
    ) -> list[dict[str, Any]]:
        search_what = self.resolve_search_what(keyword)
        url = f"https://api.adzuna.com/v1/api/jobs/{self.country_code}/search/1"
        params: dict[str, str | int] = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": search_what,
            "results_per_page": self.RESULTS_PER_PAGE,
            "content-type": "application/json",
        }
        if self.where:
            params["where"] = self.where

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, dict):
            raise ValueError("Adzuna API returned an unexpected payload.")

        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise ValueError('Adzuna API response is missing a valid "results" list.')

        return [result for result in raw_results if isinstance(result, dict)]

    async def sync_jobs(self, keyword: Optional[str] = None) -> int:
        if self._repository is None:
            raise RuntimeError("CourseRepository is required for industry_jobs sync.")

        raw_results = await self.fetch_search_results(keyword)
        jobs = [
            mapped
            for result in raw_results
            for mapped in [self.map_industry_job(result)]
            if mapped is not None
        ]

        if jobs:
            await self._repository.bulk_update_industry_jobs(
                jobs, search_role=self.resolve_search_what(keyword)
            )

        return len(jobs)

"""Four-step job market pipeline — all steps read/write industry_jobs only."""

from __future__ import annotations

import re

import numpy as np
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
from interfaces.adzuna_sync_service import AdzunaSyncService
from interfaces.embedding_service import EmbeddingService
from interfaces.job_pipeline_service import JobPipelineService
from repositories.course_repository import CourseRepository
from services.adzuna_sync_service_impl import AdzunaSyncServiceImpl

DEFAULT_SKILLS: tuple[str, ...] = (
    "Python",
    "JavaScript",
    "SQL",
    "Git",
    "Problem Solving",
    "Communication",
)

SKILL_KEYWORDS: tuple[str, ...] = (
    "Python",
    "Java",
    "React",
    "SQL",
    "FastAPI",
    "AWS",
    "Docker",
    "JavaScript",
    "C++",
    "C#",
    "HTML",
    "CSS",
    "TypeScript",
    "Kubernetes",
    "PostgreSQL",
    "Node.js",
    "Git",
    "Linux",
    "Azure",
    "GCP",
    "MongoDB",
)

_CUSTOM_SKILL_PATTERNS: dict[str, re.Pattern[str]] = {
    "C++": re.compile(r"\bc\+\+\b", re.IGNORECASE),
    "C#": re.compile(r"\bc#\b", re.IGNORECASE),
    "Node.js": re.compile(r"\bnode\.?js\b", re.IGNORECASE),
}

_SKILL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        skill,
        _CUSTOM_SKILL_PATTERNS.get(
            skill,
            re.compile(rf"\b{re.escape(skill.lower())}\b", re.IGNORECASE),
        ),
    )
    for skill in SKILL_KEYWORDS
]


class JobPipelineServiceImpl(JobPipelineService):
    def __init__(
        self,
        embedding_service: EmbeddingService,
        adzuna_service: AdzunaSyncService | None = None,
    ) -> None:
        self._embedding_service = embedding_service
        self._adzuna_service = adzuna_service or AdzunaSyncServiceImpl()

    async def sync_from_adzuna(self, db_session: Session, role_title: str) -> int:
        search_title = role_title.strip()
        raw_results = await self._adzuna_service.fetch_search_results(search_title)

        industry_jobs = [
            mapped
            for result in raw_results
            for mapped in [AdzunaSyncServiceImpl.map_industry_job(result)]
            if mapped is not None
        ]
        if not industry_jobs:
            return 0

        await CourseRepository(db_session).bulk_update_industry_jobs(industry_jobs)
        return len(industry_jobs)

    def extract_skills_from_listings(self, db_session: Session) -> int:
        jobs = (
            db_session.query(models.IndustryJob)
            .filter(
                or_(
                    models.IndustryJob.extracted_skills.is_(None),
                    models.IndustryJob.extracted_skills == "",
                    models.IndustryJob.extracted_skills == "C",
                )
            )
            .all()
        )

        for job in jobs:
            job.extracted_skills = self._extract_skills_from_text(
                job.description or "", job.title or ""
            )

        if jobs:
            db_session.commit()
        return len(jobs)

    def vectorize_listings(self, db_session: Session) -> int:
        needs_skills = (
            db_session.query(models.IndustryJob)
            .filter(
                or_(
                    models.IndustryJob.extracted_skills.is_(None),
                    models.IndustryJob.extracted_skills == "",
                    models.IndustryJob.extracted_skills == "C",
                )
            )
            .all()
        )
        for job in needs_skills:
            job.extracted_skills = self._extract_skills_from_text(
                job.description or "", job.title or ""
            )
        if needs_skills:
            db_session.commit()

        jobs = [
            job
            for job in db_session.query(models.IndustryJob)
            .filter(
                models.IndustryJob.extracted_skills.isnot(None),
                models.IndustryJob.extracted_skills != "",
            )
            .all()
            if job.feature_vector is None
            or np.allclose(job.feature_vector, 0.0)
        ]

        for job in jobs:
            job.feature_vector = self._embedding_service.get_embedding(
                self._text_for_embedding(job)
            )

        if jobs:
            db_session.commit()
        return len(jobs)

    def _collect_valid_feature_vectors(
        self, db_session: Session
    ) -> list[np.ndarray]:
        return [
            np.asarray(job.feature_vector, dtype=np.float64)
            for job in db_session.query(models.IndustryJob)
            .filter(models.IndustryJob.feature_vector.isnot(None))
            .all()
            if job.feature_vector and not np.allclose(job.feature_vector, 0.0)
        ]

    def get_average_feature_vector(self, db_session: Session) -> dict:
        vectors = self._collect_valid_feature_vectors(db_session)
        if not vectors:
            return {
                "vector": None,
                "dimension": 0,
                "job_count": 0,
                "source": "industry_jobs.feature_vector",
            }

        averaged = np.mean(np.stack(vectors), axis=0).tolist()
        return {
            "vector": averaged,
            "dimension": len(averaged),
            "job_count": len(vectors),
            "source": "industry_jobs.feature_vector",
        }

    @staticmethod
    def _extract_skills_from_text(text: str, title: str = "") -> str:
        combined = f"{title} {text}".strip()
        if not combined:
            return ", ".join(DEFAULT_SKILLS)

        matched: list[str] = []
        for skill, pattern in _SKILL_PATTERNS:
            if pattern.search(combined):
                matched.append(skill)

        if len(matched) < 2:
            return ", ".join(DEFAULT_SKILLS)
        return ", ".join(matched)

    @staticmethod
    def _text_for_embedding(job: models.IndustryJob) -> str:
        skills = (job.extracted_skills or "").strip()
        if len([s for s in skills.split(",") if s.strip()]) < 2:
            skills = ", ".join(DEFAULT_SKILLS)
        description = (job.description or "")[:800]
        return f"{job.title}. Skills: {skills}. {description}".strip()

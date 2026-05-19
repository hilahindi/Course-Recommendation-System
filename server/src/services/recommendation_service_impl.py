from __future__ import annotations

import logging
import re
from collections import Counter

import numpy as np
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import models
from interfaces.embedding_service import EmbeddingService
from interfaces.job_pipeline_service import JobPipelineService
from interfaces.recommendation_service import RecommendationService
from repositories.course_repository import CourseRepository
from services.course_service_impl import course_to_base
from services.job_pipeline_service_impl import SKILL_KEYWORDS

logger = logging.getLogger(__name__)

_PASSING_GRADE = 60
_INDUSTRY_WEIGHT = 0.7
_RATING_WEIGHT = 0.3
_MAX_RATING = 5.0
_TOP_N = 10
_ELECTIVE_CATEGORIES = ("elective", "elective1")
_MAX_MARKET_SKILLS_SHOWN = 6
_MAX_MATCHING_SKILLS_SHOWN = 5


class _MarketSkillContext:
    __slots__ = ("source", "job_count", "top_skills", "uses_live_jobs")

    def __init__(
        self,
        source: str,
        job_count: int,
        top_skills: list[str],
        uses_live_jobs: bool,
    ) -> None:
        self.source = source
        self.job_count = job_count
        self.top_skills = top_skills
        self.uses_live_jobs = uses_live_jobs


class RecommendationServiceImpl(RecommendationService):
    def __init__(
        self,
        repository: CourseRepository,
        job_pipeline: JobPipelineService,
        embedding_service: EmbeddingService,
    ) -> None:
        self._repository = repository
        self._job_pipeline = job_pipeline
        self._embedding_service = embedding_service

    async def get_personalized_recommendations(
        self, db_session: Session, student_id: int
    ) -> list[dict]:
        target_role = self._resolve_target_role(student_id)

        await self._refresh_market_data(db_session, target_role)
        industry_target_vector, market_context = self._resolve_industry_target_vector(
            db_session, target_role
        )
        passed_course_codes = self._passed_course_codes(student_id)

        candidates: list[dict] = []
        for course in self._repository.get_courses_by_categories(
            list(_ELECTIVE_CATEGORIES)
        ):
            if course.course_code in passed_course_codes:
                continue

            course_vector = self._course_feature_vector(course)
            if course_vector is None:
                continue

            vector_similarity = self._embedding_service.calculate_similarity(
                industry_target_vector,
                course_vector,
            )
            rating_normalized = min(
                1.0, max(0.0, (course.avg_rating or 0.0) / _MAX_RATING)
            )
            composite_score = (
                _INDUSTRY_WEIGHT * vector_similarity
                + _RATING_WEIGHT * rating_normalized
            )

            course_skills = self._course_skill_names(course)
            matching_skills = self._matching_skills(course_skills, market_context.top_skills)
            explanation = self._build_explanation(
                target_role, vector_similarity, rating_normalized
            )

            candidates.append(
                {
                    "course": course_to_base(course).model_dump(),
                    "score": round(composite_score * 100),
                    "explanation": explanation,
                    "matching_skills": matching_skills,
                    "vector_similarity": vector_similarity,
                    "composite_score": composite_score,
                }
            )

        candidates.sort(key=lambda item: item["composite_score"], reverse=True)
        return candidates[:_TOP_N]

    async def _refresh_market_data(self, db_session: Session, target_role: str) -> None:
        try:
            await self._job_pipeline.sync_from_adzuna(db_session, target_role)
            self._job_pipeline.extract_skills_from_listings(db_session)
            self._job_pipeline.vectorize_listings(db_session)
        except Exception as exc:
            db_session.rollback()
            logger.warning(
                "Job market sync skipped for role %r: %s", target_role, exc
            )

    def _resolve_industry_target_vector(
        self, db_session: Session, target_role: str
    ) -> tuple[list[float], _MarketSkillContext]:
        vectors = [
            np.asarray(job.feature_vector, dtype=np.float64)
            for job in db_session.query(models.IndustryJob)
            .filter(models.IndustryJob.feature_vector.isnot(None))
            .all()
            if job.feature_vector and not np.allclose(job.feature_vector, 0.0)
        ]

        market_context = self._build_market_skill_context(db_session, target_role)

        if vectors:
            return np.mean(np.stack(vectors), axis=0).tolist(), market_context

        return (
            self._embedding_service.get_embedding(
                f"{target_role} job skills requirements responsibilities"
            ),
            market_context,
        )

    def _build_market_skill_context(
        self, db_session: Session, target_role: str
    ) -> _MarketSkillContext:
        jobs = (
            db_session.query(models.IndustryJob)
            .filter(
                models.IndustryJob.extracted_skills.isnot(None),
                models.IndustryJob.extracted_skills != "",
            )
            .all()
        )

        if jobs:
            skill_counts: Counter[str] = Counter()
            for job in jobs:
                skill_counts.update(self._parse_skill_list(job.extracted_skills))
            top_skills = [
                skill for skill, _ in skill_counts.most_common(_MAX_MARKET_SKILLS_SHOWN * 2)
            ]
            return _MarketSkillContext(
                source="מודעות דרוש אמיתיות (Adzuna)",
                job_count=len(jobs),
                top_skills=top_skills,
                uses_live_jobs=True,
            )

        return _MarketSkillContext(
            source="פרופיל תפקיד היעד (הערכה כשאין מודעות דרוש)",
            job_count=0,
            top_skills=self._skills_from_role_title(target_role),
            uses_live_jobs=False,
        )

    @staticmethod
    def _build_explanation(
        target_role: str,
        vector_similarity: float,
        rating_normalized: float,
    ) -> str:
        return (
            f"הקורס מומלץ למטרה שלך להיות {target_role}.\n"
            f"{round(vector_similarity * 100)}% התאמה לביקושי כישורים בשוק העבודה "
            f"ו-{round(rating_normalized * 100)}% מדירוגי הסטודנטים."
        )

    @staticmethod
    def _parse_skill_list(skills_text: str | None) -> list[str]:
        if not skills_text:
            return []
        return [part.strip() for part in skills_text.split(",") if part.strip()]

    @staticmethod
    def _normalize_skill(skill: str) -> str:
        return re.sub(r"\s+", " ", skill.strip().lower())

    def _matching_skills(
        self, course_skills: list[str], market_skills: list[str]
    ) -> list[str]:
        if not course_skills or not market_skills:
            return []

        market_normalized = {self._normalize_skill(s): s for s in market_skills}
        matched: list[str] = []
        seen: set[str] = set()

        for course_skill in course_skills:
            course_norm = self._normalize_skill(course_skill)
            if course_norm in seen:
                continue
            for market_norm, market_label in market_normalized.items():
                if (
                    course_norm == market_norm
                    or course_norm in market_norm
                    or market_norm in course_norm
                ):
                    matched.append(course_skill)
                    seen.add(course_norm)
                    break

        return matched

    @staticmethod
    def _course_skill_names(course: models.Course) -> list[str]:
        if course.skills:
            return RecommendationServiceImpl._parse_skill_list(course.skills)
        return [skill.name for skill in course.linked_skills if skill.name]

    @staticmethod
    def _skills_from_role_title(target_role: str) -> list[str]:
        role_text = target_role.lower()
        matched = [
            skill
            for skill in SKILL_KEYWORDS
            if skill.lower() in role_text
        ]

        role_defaults: dict[str, list[str]] = {
            "cloud": ["AWS", "Docker", "Kubernetes", "Linux", "Python"],
            "cyber": ["Linux", "Python", "Network Security", "Git"],
            "security": ["Linux", "Python", "Network Security", "Git"],
            "backend": ["Python", "SQL", "PostgreSQL", "FastAPI", "Git"],
            "frontend": ["JavaScript", "React", "HTML", "CSS", "TypeScript"],
            "data": ["Python", "SQL", "PostgreSQL", "Problem Solving"],
            "devops": ["Docker", "Kubernetes", "AWS", "Linux", "Git"],
            "mobile": ["JavaScript", "React", "TypeScript", "Git"],
        }

        for keyword, skills in role_defaults.items():
            if keyword in role_text:
                for skill in skills:
                    if skill not in matched:
                        matched.append(skill)

        if len(matched) < 3:
            matched.extend(
                skill for skill in ("Python", "SQL", "Git", "Communication")
                if skill not in matched
            )

        return matched[:_MAX_MARKET_SKILLS_SHOWN * 2]

    def _course_feature_vector(self, course: models.Course) -> list[float] | None:
        if course.feature_vector and not np.allclose(course.feature_vector, 0.0):
            return course.feature_vector

        text = (course.skills or "").strip() or (course.name or "").strip()
        if not text:
            return None

        vector = self._embedding_service.get_embedding(text)
        self._repository.update_course_feature_vector(course, vector)
        return vector

    def _resolve_target_role(self, student_id: int) -> str:
        profile = self._repository.get_student_profile(student_id)
        target_role = (getattr(profile, "target_role", None) or "").strip()
        if not target_role and profile.interested_job_roles:
            target_role = profile.interested_job_roles[0].title.strip()

        if not target_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "לא נמצא תפקיד יעד בפרופיל. "
                    "השלימי את תהליך ההצטרפות ובחרי מטרת קריירה."
                ),
            )
        return target_role

    def _passed_course_codes(self, student_id: int) -> set[int]:
        history = self._repository.get_student_history(student_id)
        return {h.course_code for h in history if h.grade >= _PASSING_GRADE}

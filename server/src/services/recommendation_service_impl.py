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
from services.market_refresh import refresh_market_data
from services.recommendation_cache import get_or_compute
from services.seminar_track_catalog import (
    is_seminar_course,
    is_track_seminar_allowed,
    seminar_track_score,
    seminar_track_tier,
    target_seminar_for_tracks,
    track_names_from_profile,
    codes_match,
    LEGACY_SEMINAR_CODES,
)

logger = logging.getLogger(__name__)

_PASSING_GRADE = 60
_TRACK_WEIGHT = 0.50
_INDUSTRY_WEIGHT = 0.35
_RATING_WEIGHT = 0.15
_MAX_RATING = 5.0
_TOP_N = 10
_ELECTIVE_CATEGORIES = ("elective", "elective1", "seminar")
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
        self._defer_vector_commits = False

    async def get_personalized_recommendations(
        self, db_session: Session, student_id: int, limit: int = _TOP_N
    ) -> list[dict]:
        return await get_or_compute(
            student_id,
            limit,
            lambda: self._compute_personalized_recommendations(
                db_session, student_id, limit
            ),
        )

    async def _compute_personalized_recommendations(
        self, db_session: Session, student_id: int, limit: int
    ) -> list[dict]:
        self._defer_vector_commits = True
        try:
            return await self._build_personalized_recommendations(
                db_session, student_id, limit
            )
        finally:
            if self._defer_vector_commits:
                self._repository.commit_session()
            self._defer_vector_commits = False

    async def _build_personalized_recommendations(
        self, db_session: Session, student_id: int, limit: int
    ) -> list[dict]:
        profile = self._repository.get_student_profile(student_id)
        target_role = self._resolve_target_role_from_profile(profile)

        await self._refresh_market_data(db_session, target_role)
        industry_target_vector, market_context = self._resolve_industry_target_vector(
            db_session, target_role
        )
        passed_course_codes = self._passed_course_codes(student_id)
        track_codes, track_ids = self._track_context_for_profile(profile)
        track_names = track_names_from_profile(profile)
        has_track_preference = bool(track_codes or track_ids or track_names)
        track_w, industry_w, rating_w = self._scoring_weights(has_track_preference)

        candidates: list[dict] = []
        for course in self._repository.get_courses_by_categories(
            list(_ELECTIVE_CATEGORIES)
        ):
            if self._code_in_passed(course.course_code, passed_course_codes):
                continue

            if is_seminar_course(
                course.course_code, course.category, course.name
            ) and track_names:
                if not is_track_seminar_allowed(
                    course.course_code, track_names, course.name
                ):
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
            in_track, track_score = self._resolve_track_score(
                course, track_codes, track_ids, track_names
            )
            seminar_tier = (
                seminar_track_tier(course.course_code, track_names, course.name)
                if is_seminar_course(course.course_code, course.category, course.name)
                else None
            )
            composite_score = (
                track_w * track_score
                + industry_w * vector_similarity
                + rating_w * rating_normalized
            )

            missing_prerequisites = self._missing_prerequisites(
                course, passed_course_codes
            )
            prerequisites_met = len(missing_prerequisites) == 0

            course_skills = self._course_skill_names(course)
            matching_skills = self._matching_skills(course_skills, market_context.top_skills)

            candidates.append(
                self._build_recommendation_entry(
                    course=course,
                    target_role=target_role,
                    vector_similarity=vector_similarity,
                    rating_normalized=rating_normalized,
                    in_track=in_track,
                    track_score=track_score,
                    track_w=track_w,
                    industry_w=industry_w,
                    rating_w=rating_w,
                    missing_prerequisites=missing_prerequisites,
                    prerequisites_met=prerequisites_met,
                    matching_skills=matching_skills,
                    has_track_preference=has_track_preference,
                    composite_score=composite_score,
                    seminar_tier=seminar_tier,
                )
            )

        candidates.sort(key=lambda item: item["composite_score"], reverse=True)
        candidates = self._inject_prerequisite_courses(
            candidates,
            passed_course_codes,
            track_codes,
            track_ids,
            track_names,
            industry_target_vector,
            market_context,
            target_role,
            track_w,
            industry_w,
            rating_w,
            has_track_preference,
        )
        candidates.sort(key=lambda item: item["composite_score"], reverse=True)
        candidates = self._inject_track_seminar(
            candidates,
            passed_course_codes,
            track_names,
            track_codes,
            track_ids,
            industry_target_vector,
            market_context,
            target_role,
            track_w,
            industry_w,
            rating_w,
            has_track_preference,
        )
        candidates = self._filter_track_seminars(candidates, track_names)
        candidates.sort(key=lambda item: item["composite_score"], reverse=True)
        return candidates[:limit]

    async def _refresh_market_data(self, db_session: Session, target_role: str) -> None:
        await refresh_market_data(db_session, self._job_pipeline, target_role)

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
    def _scoring_weights(
        has_track_preference: bool,
    ) -> tuple[float, float, float]:
        if has_track_preference:
            return _TRACK_WEIGHT, _INDUSTRY_WEIGHT, _RATING_WEIGHT
        total = _INDUSTRY_WEIGHT + _RATING_WEIGHT
        return 0.0, _INDUSTRY_WEIGHT / total, _RATING_WEIGHT / total

    @staticmethod
    def _build_explanation(
        target_role: str,
        in_track: bool,
        vector_similarity: float,
        avg_rating: float,
        prerequisites_met: bool,
        missing_prerequisites: list[dict],
        has_track_preference: bool,
        seminar_tier: str | None = None,
    ) -> str:
        lines = [f"הקורס מומלץ למטרה שלך להיות {target_role}."]
        if seminar_tier == "primary":
            lines.append("סמינר מומלץ למקבץ הלימודים שבחרת בפרופיל.")
        elif seminar_tier == "fallback":
            lines.append(
                "סמינר גיבוי — מתאים כשעדיין לא עמדת בדרישות הקדם של הסמינר הייעודי למקבץ."
            )
        elif has_track_preference:
            if in_track:
                lines.append("שייך למקבץ הלימודים שבחרת בפרופיל.")
            else:
                lines.append("לא שייך למקבץ הלימודים שבחרת — מומלץ בעיקר בזכות התאמה לשוק.")
        if avg_rating > 0:
            rating_line = f"דירוג ממוצע של {avg_rating:.1f}/5 כוכבים מביקורות סטודנטים."
        else:
            rating_line = "עדיין אין דירוגים מביקורות סטודנטים."
        lines.append(
            f"{round(vector_similarity * 100)}% התאמה לביקושי כישורים בשוק העבודה. {rating_line}"
        )
        if not prerequisites_met and missing_prerequisites:
            names = ", ".join(item["name"] for item in missing_prerequisites)
            lines.append(f"דרישות קדם שטרם עמדת בהן: {names}.")
        return "\n".join(lines)

    def _build_recommendation_entry(
        self,
        *,
        course: models.Course,
        target_role: str,
        vector_similarity: float,
        rating_normalized: float,
        in_track: bool,
        track_score: float,
        track_w: float,
        industry_w: float,
        rating_w: float,
        missing_prerequisites: list[dict],
        prerequisites_met: bool,
        matching_skills: list[str],
        has_track_preference: bool,
        composite_score: float,
        seminar_tier: str | None = None,
    ) -> dict:
        explanation = self._build_explanation(
            target_role,
            in_track,
            vector_similarity,
            course.avg_rating or 0.0,
            prerequisites_met,
            missing_prerequisites,
            has_track_preference,
            seminar_tier,
        )
        entry = {
            "course": course_to_base(course).model_dump(),
            "score": round(composite_score * 100),
            "explanation": explanation,
            "matching_skills": matching_skills,
            "in_track_bundle": in_track,
            "prerequisites_met": prerequisites_met,
            "missing_prerequisites": missing_prerequisites,
            "score_breakdown": {
                "track": round(track_score * track_w * 100),
                "industry": round(vector_similarity * industry_w * 100),
                "ratings": round(rating_normalized * rating_w * 100),
            },
            "vector_similarity": vector_similarity,
            "composite_score": composite_score,
        }
        if seminar_tier:
            entry["seminar_tier"] = seminar_tier
        return entry

    def _score_course(
        self,
        course: models.Course,
        industry_target_vector: list[float],
        track_codes: set[int],
        track_ids: set[int],
        track_names: list[str],
        track_w: float,
        industry_w: float,
        rating_w: float,
    ) -> tuple[float, float, float, float, bool] | None:
        course_vector = self._course_feature_vector(course)
        if course_vector is None:
            return None

        vector_similarity = self._embedding_service.calculate_similarity(
            industry_target_vector,
            course_vector,
        )
        rating_normalized = min(
            1.0, max(0.0, (course.avg_rating or 0.0) / _MAX_RATING)
        )
        in_track, track_score = self._resolve_track_score(
            course, track_codes, track_ids, track_names
        )
        composite_score = (
            track_w * track_score
            + industry_w * vector_similarity
            + rating_w * rating_normalized
        )
        return vector_similarity, rating_normalized, track_score, composite_score, in_track

    def _inject_prerequisite_courses(
        self,
        candidates: list[dict],
        passed_course_codes: set[int],
        track_codes: set[int],
        track_ids: set[int],
        track_names: list[str],
        industry_target_vector: list[float],
        market_context: _MarketSkillContext,
        target_role: str,
        track_w: float,
        industry_w: float,
        rating_w: float,
        has_track_preference: bool,
    ) -> list[dict]:
        if not candidates:
            return candidates

        included_codes = {
            item["course"]["course_code"] for item in candidates
        }
        missing_prereq_codes: set[int] = set()

        for item in candidates:
            if item.get("prerequisites_met", True):
                continue
            for prereq in item.get("missing_prerequisites") or []:
                code = prereq["code"]
                if not self._code_in_passed(code, passed_course_codes):
                    missing_prereq_codes.add(code)

        for code in missing_prereq_codes:
            if code in included_codes:
                continue

            course = self._repository.get_course_by_code(code)
            if course is None:
                course = self._repository.get_course_by_short_code(
                    code % 100000 if code >= 100000 else code
                )
            if course is None or self._code_in_passed(course.course_code, passed_course_codes):
                continue

            if is_seminar_course(
                course.course_code, course.category, course.name
            ) and track_names:
                if not is_track_seminar_allowed(
                    course.course_code, track_names, course.name
                ):
                    continue

            scored = self._score_course(
                course,
                industry_target_vector,
                track_codes,
                track_ids,
                track_names,
                track_w,
                industry_w,
                rating_w,
            )
            if scored is None:
                continue

            vector_similarity, rating_normalized, track_score, composite_score, in_track = scored
            missing_prerequisites = self._missing_prerequisites(course, passed_course_codes)
            prerequisites_met = len(missing_prerequisites) == 0
            course_skills = self._course_skill_names(course)
            matching_skills = self._matching_skills(
                course_skills, market_context.top_skills
            )
            seminar_tier = (
                seminar_track_tier(course.course_code, track_names, course.name)
                if is_seminar_course(course.course_code, course.category, course.name)
                else None
            )

            candidates.append(
                self._build_recommendation_entry(
                    course=course,
                    target_role=target_role,
                    vector_similarity=vector_similarity,
                    rating_normalized=rating_normalized,
                    in_track=in_track,
                    track_score=track_score,
                    track_w=track_w,
                    industry_w=industry_w,
                    rating_w=rating_w,
                    missing_prerequisites=missing_prerequisites,
                    prerequisites_met=prerequisites_met,
                    matching_skills=matching_skills,
                    has_track_preference=has_track_preference,
                    composite_score=composite_score,
                    seminar_tier=seminar_tier,
                )
            )
            included_codes.add(course.course_code)

        return candidates

    @staticmethod
    def _candidate_course_code(course: dict) -> int:
        return int(course["course_code"])

    @staticmethod
    def _filter_track_seminars(
        candidates: list[dict], track_names: list[str]
    ) -> list[dict]:
        if not track_names:
            return candidates
        filtered: list[dict] = []
        for item in candidates:
            course = item["course"]
            code = RecommendationServiceImpl._candidate_course_code(course)
            if is_seminar_course(
                code, course.get("category"), course.get("name")
            ) and not is_track_seminar_allowed(
                code, track_names, course.get("name")
            ):
                continue
            filtered.append(item)
        return filtered

    def _inject_track_seminar(
        self,
        candidates: list[dict],
        passed_course_codes: set[int],
        track_names: list[str],
        track_codes: set[int],
        track_ids: set[int],
        industry_target_vector: list[float],
        market_context: _MarketSkillContext,
        target_role: str,
        track_w: float,
        industry_w: float,
        rating_w: float,
        has_track_preference: bool,
    ) -> list[dict]:
        if not track_names or self._has_passed_seminar(passed_course_codes):
            return candidates

        seminar_code = target_seminar_for_tracks(track_names)

        course = self._find_seminar_course(seminar_code)
        if course is None or self._code_in_passed(course.course_code, passed_course_codes):
            return candidates

        candidates = [
            item
            for item in candidates
            if not is_seminar_course(
                self._candidate_course_code(item["course"]),
                item["course"].get("category"),
                item["course"].get("name"),
            )
        ]

        if any(
            codes_match(
                course.course_code,
                self._candidate_course_code(item["course"]),
            )
            for item in candidates
        ):
            return candidates

        scored = self._score_course(
            course,
            industry_target_vector,
            track_codes,
            track_ids,
            track_names,
            track_w,
            industry_w,
            rating_w,
        )
        if scored is None:
            return candidates

        vector_similarity, rating_normalized, track_score, composite_score, in_track = scored
        missing_prerequisites = self._missing_prerequisites(course, passed_course_codes)
        prerequisites_met = len(missing_prerequisites) == 0
        course_skills = self._course_skill_names(course)
        matching_skills = self._matching_skills(course_skills, market_context.top_skills)
        seminar_tier = seminar_track_tier(course.course_code, track_names, course.name)

        entry = self._build_recommendation_entry(
            course=course,
            target_role=target_role,
            vector_similarity=vector_similarity,
            rating_normalized=rating_normalized,
            in_track=in_track,
            track_score=track_score,
            track_w=track_w,
            industry_w=industry_w,
            rating_w=rating_w,
            missing_prerequisites=missing_prerequisites,
            prerequisites_met=prerequisites_met,
            matching_skills=matching_skills,
            has_track_preference=has_track_preference,
            composite_score=composite_score,
            seminar_tier=seminar_tier,
        )
        candidates.insert(0, entry)
        return candidates

    @staticmethod
    def _curriculum_name_to_code() -> dict[str, int]:
        from services.elective_curriculum_catalog import ELECTIVE_CURRICULUM
        from services.mandatory_curriculum_catalog import MANDATORY_CURRICULUM

        mapping: dict[str, int] = {}
        for spec in (*MANDATORY_CURRICULUM, *ELECTIVE_CURRICULUM):
            mapping[spec.name] = spec.code
            for alias in spec.aliases:
                mapping[alias] = spec.code
        return mapping

    def _find_seminar_course(self, code: int) -> models.Course | None:
        course = self._repository.get_course_by_short_code(code)
        if course:
            return course
        for legacy in LEGACY_SEMINAR_CODES:
            if codes_match(code, legacy):
                legacy_course = self._repository.get_course_by_short_code(legacy)
                if legacy_course:
                    return legacy_course
        return None

    def _has_passed_seminar(self, passed_course_codes: set[int]) -> bool:
        for course in self._repository.get_courses_by_categories(
            list(_ELECTIVE_CATEGORIES)
        ):
            if not is_seminar_course(
                course.course_code, course.category, course.name
            ):
                continue
            if self._code_in_passed(course.course_code, passed_course_codes):
                return True
        return False

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
        self._repository.update_course_feature_vector(
            course, vector, commit=not self._defer_vector_commits
        )
        return vector

    def _resolve_target_role(self, student_id: int) -> str:
        profile = self._repository.get_student_profile(student_id)
        return self._resolve_target_role_from_profile(profile)

    @staticmethod
    def _resolve_target_role_from_profile(profile) -> str:
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

    @staticmethod
    def _track_context_for_profile(profile) -> tuple[set[int], set[int]]:
        from services.track_courses_catalog import TRACK_COURSES

        track_codes: set[int] = set()
        track_ids: set[int] = set()
        for track in profile.interested_tracks or []:
            track_ids.add(track.id)
            for entry in TRACK_COURSES.get(track.name, ()):
                track_codes.add(entry.code)
                if entry.code >= 100000:
                    track_codes.add(entry.code % 100000)
        return track_codes, track_ids

    @staticmethod
    def _resolve_track_score(
        course: models.Course,
        track_codes: set[int],
        track_ids: set[int],
        track_names: list[str],
    ) -> tuple[bool, float]:
        if (course.category or "") == "seminar" or is_seminar_course(
            course.course_code, course.category, course.name
        ):
            score = seminar_track_score(course.course_code, track_names, course.name)
            if score > 0:
                return True, score

        in_track = RecommendationServiceImpl._course_in_track_bundle(
            course, track_codes, track_ids
        )
        return in_track, 1.0 if in_track else 0.0

    @staticmethod
    def _course_in_track_bundle(
        course: models.Course,
        track_codes: set[int],
        track_ids: set[int],
    ) -> bool:
        code = course.course_code
        short_code = code % 100000 if code >= 100000 else code
        if code in track_codes or short_code in track_codes:
            return True
        course_track_ids = {track.id for track in course.tracks or []}
        return bool(course_track_ids & track_ids)

    @staticmethod
    def _code_in_passed(code: int, passed_codes: set[int]) -> bool:
        short_code = code % 100000 if code >= 100000 else code
        return code in passed_codes or short_code in passed_codes

    def _passed_course_codes(self, student_id: int) -> set[int]:
        history = self._repository.get_student_history(student_id)
        codes: set[int] = set()
        for entry in history:
            if entry.grade >= _PASSING_GRADE:
                codes.add(entry.course_code)
                if entry.course_code >= 100000:
                    codes.add(entry.course_code % 100000)
        return codes

    @staticmethod
    def _missing_prerequisites(
        course: models.Course, passed_codes: set[int]
    ) -> list[dict]:
        missing: list[dict] = []
        for prereq in course.prerequisite_courses or []:
            code = prereq.course_code
            short_code = code % 100000 if code >= 100000 else code
            if code not in passed_codes and short_code not in passed_codes:
                missing.append({"code": code, "name": prereq.name})
        return missing

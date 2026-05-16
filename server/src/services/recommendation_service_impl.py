import re
from typing import List

from dtos import CourseBase, RecommendationResponse
from interfaces.recommendation_service import RecommendationService
from repositories.course_repository import CourseRepository


class RecommendationServiceImpl(RecommendationService):
    def __init__(self, repository: CourseRepository):
        self._repository = repository

    def get_recommendations(self, student_id: int) -> List[RecommendationResponse]:
        courses = self._repository.get_courses()
        history = self._repository.get_student_history(student_id)
        profile = self._repository.get_student_profile(student_id)

        passed_course_codes = {h.course_code for h in history if h.grade >= 60}
        interested_track_ids = {t.id for t in profile.interested_tracks}
        interested_job_roles = profile.interested_job_roles
        target_role_names = [jr.title for jr in interested_job_roles]
        target_skill_ids = {
            s.id for jr in interested_job_roles for s in jr.skills
        }

        recommended: List[RecommendationResponse] = []

        for course in courses:
            if course.course_code in passed_course_codes:
                continue

            if course.prerequisites:
                prereq_codes = [
                    int(p) for p in re.findall(r"\d{4,5}", course.prerequisites)
                ]
                if prereq_codes and not all(
                    p in passed_course_codes for p in prereq_codes
                ):
                    continue

            score = 0
            course_skill_ids = {s.id for s in course.skills}
            if course_skill_ids & target_skill_ids:
                score += 35

            if course.track_id and course.track_id in interested_track_ids:
                score += 25

            if course.skills:
                score += min(20, len(course.skills) * 5)

            reviews = self._repository.get_course_reviews(course.course_code)
            if reviews:
                avg_rating = sum(r.rating for r in reviews) / len(reviews)
                score += int(avg_rating * 2)
            else:
                score += 6

            if profile.target_workload >= course.workload:
                score += 5
            if not profile.needs_flexible_attendance or not course.mandatory_attendance:
                score += 5

            course_skill_names = [s.name for s in course.skills]
            top_skill = (
                course_skill_names[0] if course_skill_names else "Technical Knowledge"
            )
            target_role = target_role_names[0] if target_role_names else "Professional"
            explanation = (
                f"This course is recommended because it boosts your {top_skill} "
                f"and aligns with your goal of becoming a {target_role}."
            )

            if score > 0:
                recommended.append(
                    RecommendationResponse(
                        course=CourseBase.model_validate(course),
                        score=score,
                        explanation=explanation,
                    )
                )

        recommended.sort(key=lambda item: item.score, reverse=True)
        return recommended

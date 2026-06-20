from typing import Dict, List

from sqlalchemy.orm import Session

import models
from dtos import (
    CourseBase,
    CoursePipelineSeedResult,
    CoursePipelineStepResult,
    CourseReviewBulkCreate,
    CourseReviewCreate,
    CourseReviewDeleteAllResult,
    CourseReviewResponse,
    CourseReviewSeedResult,
)
from interfaces.course_service import CourseService
from repositories.course_repository import CourseRepository
from services.course_pipeline_service import CoursePipelineService
from services.courses_list_cache import get_or_load_courses


def course_to_base(course) -> CourseBase:
    from dtos import SkillBase
    from services.course_skills_by_name import parse_skill_names

    track_ids = [t.id for t in getattr(course, "tracks", []) or []]
    prereq_codes = [
        p.course_code for p in getattr(course, "prerequisite_courses", []) or []
    ]
    skills_payload = [
        SkillBase(id=index, name=name)
        for index, name in enumerate(parse_skill_names(course.skills or ""), start=1)
    ]

    return CourseBase(
        course_code=course.course_code,
        name=course.name,
        category=course.category,
        workload=course.workload or 0,
        credits=float(course.credits or 3),
        semester_hours=course.semester_hours or course.workload or 3,
        mandatory_attendance=bool(course.mandatory_attendance),
        prerequisites=course.prerequisites or "",
        has_exam=course.has_exam if course.has_exam is not None else True,
        final_task_description=course.final_task_description,
        track_id=track_ids[0] if track_ids else course.track_id,
        track_ids=track_ids,
        prerequisite_course_codes=prereq_codes,
        day_of_week=course.day_of_week,
        start_time=course.start_time,
        end_time=course.end_time,
        room=course.room,
        lecturer=course.lecturer,
        occurrences=[],
        skills=skills_payload,
    )


def submit_course_review(
    db_session: Session,
    student_id: int,
    course_code: int,
    rating: int,
    review_text: str,
    is_anonymous: bool,
) -> models.CourseReview:
    """Persist a student course review (rating, text, anonymity)."""
    repository = CourseRepository(db_session)
    return repository.create_course_review(
        student_id,
        CourseReviewCreate(
            course_code=course_code,
            rating=rating,
            review_text=review_text,
            is_anonymous=is_anonymous,
        ),
    )


class CourseServiceImpl(CourseService):
    def __init__(
        self,
        repository: CourseRepository,
        pipeline: CoursePipelineService,
    ):
        self._repository = repository
        self._pipeline = pipeline

    def list_courses(self) -> List[CourseBase]:
        return get_or_load_courses(
            lambda: [course_to_base(course) for course in self._repository.get_courses()]
        )

    def get_yearly_mandatory_courses(self) -> Dict[int, List[int]]:
        return self._repository.get_yearly_mandatory_map()

    def get_reviews(self, course_code: int) -> List[CourseReviewResponse]:
        reviews = self._repository.get_course_reviews(course_code)
        return [self._to_review_response(review) for review in reviews]

    def create_review(
        self, course_code: int, student_id: int, review: CourseReviewCreate
    ) -> CourseReviewResponse:
        saved = self._repository.create_course_review(student_id, review)
        return self._to_review_response(saved)

    def submit_course_review(
        self,
        student_id: int,
        course_code: int,
        rating: int,
        review_text: str,
        is_anonymous: bool,
    ) -> CourseReviewResponse:
        saved = submit_course_review(
            self._repository._db,
            student_id,
            course_code,
            rating,
            review_text,
            is_anonymous,
        )
        return self._to_review_response(saved)

    def create_reviews_bulk(
        self, student_id: int, bulk: CourseReviewBulkCreate
    ) -> List[CourseReviewResponse]:
        saved: List[CourseReviewResponse] = []
        for item in bulk.reviews:
            if not self._repository.get_course_by_code(item.course_code):
                raise ValueError(f"Course {item.course_code} not found")
            review = self._repository.create_course_review(
                student_id,
                CourseReviewCreate(
                    course_code=item.course_code,
                    rating=item.rating,
                    review_text=item.review_text,
                    is_anonymous=item.is_anonymous,
                ),
            )
            saved.append(self._to_review_response(review))

        if saved:
            avg = self._repository.get_average_ratings_by_course()
            for response in saved:
                self._repository.update_course_avg_rating(
                    response.course_code,
                    avg.get(response.course_code, 0.0),
                )

        return saved

    def seed_all_course_reviews(
        self, db_session: Session
    ) -> CourseReviewSeedResult:
        result = self._pipeline.seed_reviews_for_all_courses(db_session)
        return CourseReviewSeedResult(**result)

    def delete_all_reviews(self) -> CourseReviewDeleteAllResult:
        deleted = self._repository.delete_all_course_reviews()
        return CourseReviewDeleteAllResult(
            status="success",
            reviews_deleted=deleted,
            message=f"Deleted {deleted} review(s).",
        )

    def run_pipeline_seed(self, db_session: Session) -> CoursePipelineSeedResult:
        result = self._pipeline.seed_initial_courses_and_reviews(db_session)
        return CoursePipelineSeedResult(**result)

    def run_pipeline_extract_skills(self, db_session: Session) -> CoursePipelineStepResult:
        count = self._pipeline.extract_course_skills(db_session)
        return CoursePipelineStepResult(
            status="success",
            updated_count=count,
            message=f"Updated skills for {count} course(s).",
        )

    def run_pipeline_vectorize(self, db_session: Session) -> CoursePipelineStepResult:
        count = self._pipeline.vectorize_courses(db_session)
        return CoursePipelineStepResult(
            status="success",
            updated_count=count,
            message=f"Vectorized {count} course(s).",
        )

    def run_pipeline_compile_ratings(self, db_session: Session) -> CoursePipelineStepResult:
        count = self._pipeline.compile_course_ratings(db_session)
        return CoursePipelineStepResult(
            status="success",
            updated_count=count,
            message=f"Compiled average ratings for {count} course(s).",
        )

    @staticmethod
    def _to_review_response(review) -> CourseReviewResponse:
        name = (
            "Anonymous"
            if review.is_anonymous
            else (review.student.name if review.student else "Unknown")
        )
        return CourseReviewResponse(
            id=review.id,
            student_id=review.student_id,
            course_code=review.course_code,
            rating=review.rating,
            review_text=review.review_text,
            is_anonymous=review.is_anonymous,
            student_name=name,
        )

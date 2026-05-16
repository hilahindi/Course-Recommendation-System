from typing import Dict, List

from dtos import CourseBase, CourseReviewCreate, CourseReviewResponse
from interfaces.course_service import CourseService
from repositories.course_repository import CourseRepository


class CourseServiceImpl(CourseService):
    def __init__(self, repository: CourseRepository):
        self._repository = repository

    def list_courses(self) -> List[CourseBase]:
        return [
            CourseBase.model_validate(course)
            for course in self._repository.get_courses()
        ]

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

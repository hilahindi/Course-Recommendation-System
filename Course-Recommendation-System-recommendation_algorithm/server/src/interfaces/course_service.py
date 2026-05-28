from abc import ABC, abstractmethod
from typing import Dict, List

from sqlalchemy.orm import Session

from dtos import (
    BulkReviewItem,
    BulkReviewResult,
    CourseBase,
    CoursePipelineSeedResult,
    CoursePipelineStepResult,
    CourseReviewCreate,
    CourseReviewResponse,
)


class CourseService(ABC):
    """Application service contract for course operations."""

    @abstractmethod
    def list_courses(self) -> List[CourseBase]:
        ...

    @abstractmethod
    def get_yearly_mandatory_courses(self) -> Dict[int, List[int]]:
        ...

    @abstractmethod
    def get_reviews(self, course_code: int) -> List[CourseReviewResponse]:
        ...

    @abstractmethod
    def create_review(
        self, course_code: int, student_id: int, review: CourseReviewCreate
    ) -> CourseReviewResponse:
        ...

    @abstractmethod
    def submit_course_review(
        self,
        student_id: int,
        course_code: int,
        rating: int,
        review_text: str,
        is_anonymous: bool,
    ) -> CourseReviewResponse:
        ...

    @abstractmethod
    def bulk_create_reviews(self, reviews: List[BulkReviewItem]) -> BulkReviewResult:
        ...

    @abstractmethod
    def run_pipeline_seed(self, db_session: Session) -> CoursePipelineSeedResult:
        ...

    @abstractmethod
    def run_pipeline_extract_skills(self, db_session: Session) -> CoursePipelineStepResult:
        ...

    @abstractmethod
    def run_pipeline_vectorize(self, db_session: Session) -> CoursePipelineStepResult:
        ...

    @abstractmethod
    def run_pipeline_compile_ratings(self, db_session: Session) -> CoursePipelineStepResult:
        ...

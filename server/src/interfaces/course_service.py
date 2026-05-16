from abc import ABC, abstractmethod
from typing import Any, Dict, List

from dtos import CourseBase, CourseReviewCreate, CourseReviewResponse


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

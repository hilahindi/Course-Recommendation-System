from abc import ABC, abstractmethod
from typing import List

from dtos import (
    PlannedCourseBase,
    PlannedCourseResponse,
    StudentCourseHistoryBulkCreate,
    StudentCourseHistoryCreate,
    StudentCourseHistoryResponse,
    StudentProfileResponse,
    StudentProfileUpdate,
)


class ProfileService(ABC):
    """Application service contract for student profile operations."""

    @abstractmethod
    def get_profile(self, student_id: int) -> StudentProfileResponse:
        ...

    @abstractmethod
    def update_profile(
        self, student_id: int, profile_update: StudentProfileUpdate
    ) -> StudentProfileResponse:
        ...

    @abstractmethod
    def get_history(self, student_id: int) -> List[StudentCourseHistoryResponse]:
        ...

    @abstractmethod
    def add_history(
        self, student_id: int, history_create: StudentCourseHistoryCreate
    ) -> StudentCourseHistoryResponse:
        ...

    @abstractmethod
    def add_history_bulk(
        self, student_id: int, bulk_create: StudentCourseHistoryBulkCreate
    ) -> List[StudentCourseHistoryResponse]:
        ...

    @abstractmethod
    def remove_history(self, student_id: int, course_code: int) -> None:
        ...

    @abstractmethod
    def get_schedule(self, student_id: int) -> List[PlannedCourseResponse]:
        ...

    @abstractmethod
    def add_schedule(
        self, student_id: int, course: PlannedCourseBase
    ) -> PlannedCourseResponse:
        ...

    @abstractmethod
    def remove_schedule(self, student_id: int, course_code: int) -> None:
        ...

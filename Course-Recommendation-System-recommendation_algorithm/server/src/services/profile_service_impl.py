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
from interfaces.profile_service import ProfileService
from repositories.course_repository import CourseRepository


class ProfileServiceImpl(ProfileService):
    def __init__(self, repository: CourseRepository):
        self._repository = repository

    def get_profile(self, student_id: int) -> StudentProfileResponse:
        return StudentProfileResponse.model_validate(
            self._repository.get_student_profile(student_id)
        )

    def update_profile(
        self, student_id: int, profile_update: StudentProfileUpdate
    ) -> StudentProfileResponse:
        profile = self._repository.update_student_profile(student_id, profile_update)
        return StudentProfileResponse.model_validate(profile)

    def get_history(self, student_id: int) -> List[StudentCourseHistoryResponse]:
        return [
            StudentCourseHistoryResponse.model_validate(h)
            for h in self._repository.get_student_history(student_id)
        ]

    def add_history(
        self, student_id: int, history_create: StudentCourseHistoryCreate
    ) -> StudentCourseHistoryResponse:
        history = self._repository.add_student_course_history(
            student_id, history_create
        )
        return StudentCourseHistoryResponse.model_validate(history)

    def add_history_bulk(
        self, student_id: int, bulk_create: StudentCourseHistoryBulkCreate
    ) -> List[StudentCourseHistoryResponse]:
        histories = self._repository.add_student_course_history_bulk(
            student_id, bulk_create
        )
        return [StudentCourseHistoryResponse.model_validate(h) for h in histories]

    def get_schedule(self, student_id: int) -> List[PlannedCourseResponse]:
        return [
            PlannedCourseResponse.model_validate(p)
            for p in self._repository.get_planned_courses(student_id)
        ]

    def add_schedule(
        self, student_id: int, course: PlannedCourseBase
    ) -> PlannedCourseResponse:
        planned = self._repository.add_planned_course(student_id, course.course_code)
        return PlannedCourseResponse.model_validate(planned)

    def remove_schedule(self, student_id: int, course_code: int) -> None:
        self._repository.remove_planned_course(student_id, course_code)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from dtos import (
    PlannedCourseBase,
    PlannedCourseResponse,
    StudentCourseHistoryBulkCreate,
    StudentCourseHistoryCreate,
    StudentCourseHistoryResponse,
    StudentProfileResponse,
    StudentProfileUpdate,
)
from repositories.course_repository import CourseRepository

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


def get_repository(db: Session = Depends(get_db)) -> CourseRepository:
    return CourseRepository(db)


@router.get("/{student_id}", response_model=StudentProfileResponse)
def read_profile(
    student_id: int, repository: CourseRepository = Depends(get_repository)
):
    return repository.get_student_profile(student_id)


@router.put("/{student_id}", response_model=StudentProfileResponse)
def update_profile(
    student_id: int,
    profile_update: StudentProfileUpdate,
    repository: CourseRepository = Depends(get_repository),
):
    return repository.update_student_profile(student_id, profile_update)


@router.get("/{student_id}/history", response_model=List[StudentCourseHistoryResponse])
def read_history(
    student_id: int, repository: CourseRepository = Depends(get_repository)
):
    return repository.get_student_history(student_id)


@router.post("/{student_id}/history", response_model=StudentCourseHistoryResponse)
def add_history(
    student_id: int,
    history_create: StudentCourseHistoryCreate,
    repository: CourseRepository = Depends(get_repository),
):
    return repository.add_student_course_history(student_id, history_create)


@router.post(
    "/{student_id}/history/bulk", response_model=List[StudentCourseHistoryResponse]
)
def add_history_bulk(
    student_id: int,
    bulk_create: StudentCourseHistoryBulkCreate,
    repository: CourseRepository = Depends(get_repository),
):
    return repository.add_student_course_history_bulk(student_id, bulk_create)


@router.get("/{student_id}/schedule", response_model=List[PlannedCourseResponse])
def get_schedule(
    student_id: int, repository: CourseRepository = Depends(get_repository)
):
    return repository.get_planned_courses(student_id)


@router.post("/{student_id}/schedule", response_model=PlannedCourseResponse)
def add_schedule(
    student_id: int,
    course: PlannedCourseBase,
    repository: CourseRepository = Depends(get_repository),
):
    return repository.add_planned_course(student_id, course.course_code)


@router.delete("/{student_id}/schedule/{course_code}")
def remove_schedule(
    student_id: int,
    course_code: int,
    repository: CourseRepository = Depends(get_repository),
):
    repository.remove_planned_course(student_id, course_code)
    return {"status": "ok"}

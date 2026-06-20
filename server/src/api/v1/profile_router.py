from fastapi import APIRouter, Depends
from typing import List

from dependencies import get_profile_service
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

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("/{student_id}", response_model=StudentProfileResponse)
def read_profile(
    student_id: int, profile_service: ProfileService = Depends(get_profile_service)
):
    return profile_service.get_profile(student_id)


@router.put("/{student_id}", response_model=StudentProfileResponse)
def update_profile(
    student_id: int,
    profile_update: StudentProfileUpdate,
    profile_service: ProfileService = Depends(get_profile_service),
):
    return profile_service.update_profile(student_id, profile_update)


@router.get("/{student_id}/history", response_model=List[StudentCourseHistoryResponse])
def read_history(
    student_id: int, profile_service: ProfileService = Depends(get_profile_service)
):
    return profile_service.get_history(student_id)


@router.post("/{student_id}/history", response_model=StudentCourseHistoryResponse)
def add_history(
    student_id: int,
    history_create: StudentCourseHistoryCreate,
    profile_service: ProfileService = Depends(get_profile_service),
):
    return profile_service.add_history(student_id, history_create)


@router.post(
    "/{student_id}/history/bulk", response_model=List[StudentCourseHistoryResponse]
)
def add_history_bulk(
    student_id: int,
    bulk_create: StudentCourseHistoryBulkCreate,
    profile_service: ProfileService = Depends(get_profile_service),
):
    return profile_service.add_history_bulk(student_id, bulk_create)


@router.delete("/{student_id}/history/{course_code}")
def remove_history(
    student_id: int,
    course_code: int,
    profile_service: ProfileService = Depends(get_profile_service),
):
    profile_service.remove_history(student_id, course_code)
    return {"status": "ok"}


@router.get("/{student_id}/schedule", response_model=List[PlannedCourseResponse])
def get_schedule(
    student_id: int, profile_service: ProfileService = Depends(get_profile_service)
):
    return profile_service.get_schedule(student_id)


@router.post("/{student_id}/schedule", response_model=PlannedCourseResponse)
def add_schedule(
    student_id: int,
    course: PlannedCourseBase,
    profile_service: ProfileService = Depends(get_profile_service),
):
    return profile_service.add_schedule(student_id, course)


@router.delete("/{student_id}/schedule/{course_code}")
def remove_schedule(
    student_id: int,
    course_code: int,
    profile_service: ProfileService = Depends(get_profile_service),
):
    profile_service.remove_schedule(student_id, course_code)
    return {"status": "ok"}

from fastapi import APIRouter, Depends
from typing import List

from database import get_db
from dependencies import (
    get_job_pipeline_service,
    get_profile_service,
    verify_student_access,
)
from dtos import (
    PlannedCourseBase,
    PlannedCourseResponse,
    StudentCourseHistoryBulkCreate,
    StudentCourseHistoryCreate,
    StudentCourseHistoryResponse,
    StudentProfileResponse,
    StudentProfileUpdate,
)
from interfaces.job_pipeline_service import JobPipelineService
from interfaces.profile_service import ProfileService
from services.cache_invalidation import invalidate_student_caches
from services.market_refresh import refresh_market_data, target_role_from_job_role_ids
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/v1/profile",
    tags=["profile"],
    dependencies=[Depends(verify_student_access)],
)


def _job_role_ids(profile: StudentProfileResponse) -> tuple[int, ...]:
    return tuple(sorted(role.id for role in profile.interested_job_roles))


@router.get("/{student_id}", response_model=StudentProfileResponse)
def read_profile(
    student_id: int, profile_service: ProfileService = Depends(get_profile_service)
):
    return profile_service.get_profile(student_id)


@router.put("/{student_id}", response_model=StudentProfileResponse)
async def update_profile(
    student_id: int,
    profile_update: StudentProfileUpdate,
    db: Session = Depends(get_db),
    profile_service: ProfileService = Depends(get_profile_service),
    job_pipeline: JobPipelineService = Depends(get_job_pipeline_service),
):
    before = profile_service.get_profile(student_id)
    before_roles = _job_role_ids(before)

    result = profile_service.update_profile(student_id, profile_update)
    invalidate_student_caches(student_id, refresh_market=True)

    after_roles = _job_role_ids(result)
    if after_roles != before_roles:
        target_role = (
            result.interested_job_roles[0].title.strip()
            if result.interested_job_roles
            else target_role_from_job_role_ids(
                db, profile_update.interested_job_role_ids
            )
        )
        if target_role:
            await refresh_market_data(
                db, job_pipeline, target_role, force_adzuna=True
            )

    return result


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
    result = profile_service.add_history(student_id, history_create)
    invalidate_student_caches(student_id)
    return result


@router.post(
    "/{student_id}/history/bulk", response_model=List[StudentCourseHistoryResponse]
)
def add_history_bulk(
    student_id: int,
    bulk_create: StudentCourseHistoryBulkCreate,
    profile_service: ProfileService = Depends(get_profile_service),
):
    result = profile_service.add_history_bulk(student_id, bulk_create)
    invalidate_student_caches(student_id)
    return result


@router.delete("/{student_id}/history/{course_code}")
def remove_history(
    student_id: int,
    course_code: int,
    profile_service: ProfileService = Depends(get_profile_service),
):
    profile_service.remove_history(student_id, course_code)
    invalidate_student_caches(student_id)
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

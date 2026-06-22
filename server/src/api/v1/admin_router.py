"""Admin-only endpoints: curriculum (course) management and user roles.

Every route requires an authenticated user whose role is 'admin' (enforced by
the router-level require_admin dependency).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_course_repository, require_admin
from dtos import (
    AdminUserResponse,
    CourseAdminCreate,
    CourseAdminUpsert,
    CourseBase,
    UserRoleUpdate,
)
from repositories.course_repository import CourseRepository
from services import recommendation_cache, roadmap_cache
from services.course_service_impl import course_to_base
from services.courses_list_cache import invalidate_courses_list_cache

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


def _invalidate_catalog_caches() -> None:
    """Catalog changed → drop cached course list and derived recommendations."""
    invalidate_courses_list_cache()
    recommendation_cache.invalidate()
    roadmap_cache.invalidate()


# --- Course management ---


@router.post("/courses", response_model=CourseBase, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseAdminCreate,
    repo: CourseRepository = Depends(get_course_repository),
):
    if repo.get_course_by_code(payload.course_code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Course code already exists"
        )
    course = repo.create_course(payload.model_dump())
    _invalidate_catalog_caches()
    return course_to_base(course)


@router.put("/courses/{course_code}", response_model=CourseBase)
def update_course(
    course_code: int,
    payload: CourseAdminUpsert,
    repo: CourseRepository = Depends(get_course_repository),
):
    course = repo.update_course(course_code, payload.model_dump())
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    _invalidate_catalog_caches()
    return course_to_base(course)


@router.delete("/courses/{course_code}")
def delete_course(
    course_code: int,
    repo: CourseRepository = Depends(get_course_repository),
):
    if not repo.delete_course(course_code):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    _invalidate_catalog_caches()
    return {"status": "ok", "deleted_course_code": course_code}


# --- User / role management ---


@router.get("/users", response_model=List[AdminUserResponse])
def list_users(repo: CourseRepository = Depends(get_course_repository)):
    return repo.list_students()


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def set_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    repo: CourseRepository = Depends(get_course_repository),
):
    student = repo.set_student_role(user_id, payload.role)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return student

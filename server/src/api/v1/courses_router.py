from fastapi import APIRouter, Depends, HTTPException
from typing import List

from dependencies import get_course_service
from dtos import CourseBase, CourseReviewCreate, CourseReviewResponse
from interfaces.course_service import CourseService

router = APIRouter(prefix="/api/v1/courses", tags=["courses"])


@router.get("/", response_model=List[CourseBase])
def read_courses(course_service: CourseService = Depends(get_course_service)):
    return course_service.list_courses()


@router.get("/yearly-mandatory")
def get_yearly_mandatory_courses(
    course_service: CourseService = Depends(get_course_service),
):
    return course_service.get_yearly_mandatory_courses()


@router.get("/{course_code}/reviews", response_model=List[CourseReviewResponse])
def read_course_reviews(
    course_code: int,
    course_service: CourseService = Depends(get_course_service),
):
    return course_service.get_reviews(course_code)


@router.post("/{course_code}/reviews", response_model=CourseReviewResponse)
def create_course_review(
    course_code: int,
    student_id: int,
    review: CourseReviewCreate,
    course_service: CourseService = Depends(get_course_service),
):
    if course_code != review.course_code:
        raise HTTPException(status_code=400, detail="Course code mismatch")
    return course_service.create_review(course_code, student_id, review)

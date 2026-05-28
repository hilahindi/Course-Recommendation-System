from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_course_service, get_current_student_id
from dtos import (
    BulkReviewItem,
    BulkReviewResult,
    CourseBase,
    CoursePipelineSeedResult,
    CoursePipelineStepResult,
    CourseReviewCreate,
    CourseReviewResponse,
    CourseReviewSubmit,
)
from interfaces.course_service import CourseService

router = APIRouter(prefix="/api/v1/courses", tags=["courses"])
reviews_router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])
course_pipeline_router = APIRouter(
    prefix="/api/v1/course-pipeline", tags=["course-pipeline"]
)


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
    review: CourseReviewCreate,
    student_id: int = Depends(get_current_student_id),
    course_service: CourseService = Depends(get_course_service),
):
    if course_code != review.course_code:
        raise HTTPException(status_code=400, detail="Course code mismatch")
    return course_service.create_review(course_code, student_id, review)


@reviews_router.post("/submit", response_model=CourseReviewResponse)
def submit_review(
    body: CourseReviewSubmit,
    student_id: int = Depends(get_current_student_id),
    course_service: CourseService = Depends(get_course_service),
):
    return course_service.submit_course_review(
        student_id=student_id,
        course_code=body.course_code,
        rating=body.rating,
        review_text=body.review_text,
        is_anonymous=body.is_anonymous,
    )


@reviews_router.post("/bulk", response_model=BulkReviewResult, status_code=status.HTTP_200_OK)
def bulk_create_reviews(
    reviews: List[BulkReviewItem],
    course_service: CourseService = Depends(get_course_service),
):
    return course_service.bulk_create_reviews(reviews)


@course_pipeline_router.post(
    "/seed", response_model=CoursePipelineSeedResult, status_code=status.HTTP_200_OK
)
def seed_courses_and_reviews(
    db: Session = Depends(get_db),
    course_service: CourseService = Depends(get_course_service),
):
    try:
        return course_service.run_pipeline_seed(db)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Course seed failed: {exc}",
        ) from exc


@course_pipeline_router.post(
    "/extract-skills",
    response_model=CoursePipelineStepResult,
    status_code=status.HTTP_200_OK,
)
def extract_course_skills(
    db: Session = Depends(get_db),
    course_service: CourseService = Depends(get_course_service),
):
    try:
        return course_service.run_pipeline_extract_skills(db)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Skill extraction failed: {exc}",
        ) from exc


@course_pipeline_router.post(
    "/vectorize",
    response_model=CoursePipelineStepResult,
    status_code=status.HTTP_200_OK,
)
def vectorize_courses(
    db: Session = Depends(get_db),
    course_service: CourseService = Depends(get_course_service),
):
    try:
        return course_service.run_pipeline_vectorize(db)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Course vectorization failed: {exc}",
        ) from exc


@course_pipeline_router.post(
    "/compile-ratings",
    response_model=CoursePipelineStepResult,
    status_code=status.HTTP_200_OK,
)
def compile_course_ratings(
    db: Session = Depends(get_db),
    course_service: CourseService = Depends(get_course_service),
):
    try:
        return course_service.run_pipeline_compile_ratings(db)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rating compilation failed: {exc}",
        ) from exc

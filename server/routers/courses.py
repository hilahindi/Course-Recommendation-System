from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

import crud, schemas
from database import get_db

router = APIRouter(
    prefix="/api/courses",
    tags=["courses"]
)

@router.get("/", response_model=List[schemas.CourseBase])
def read_courses(db: Session = Depends(get_db)):
    return crud.get_courses(db)

@router.get("/{course_code}/reviews", response_model=List[schemas.CourseReviewResponse])
def read_course_reviews(course_code: int, db: Session = Depends(get_db)):
    return crud.get_course_reviews(db, course_code)

@router.post("/{course_code}/reviews", response_model=schemas.CourseReviewResponse)
def create_course_review(course_code: int, student_id: int, review: schemas.CourseReviewCreate, db: Session = Depends(get_db)):
    if review.course_code != course_code:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Course code mismatch")
    return crud.create_course_review(db, student_id, review)

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
    reviews = crud.get_course_reviews(db, course_code)
    # Map student name or anonymous
    result = []
    for r in reviews:
        name = "Anonymous" if r.is_anonymous else (r.student.name if r.student else "Unknown")
        result.append({
            "id": r.id,
            "student_id": r.student_id,
            "course_code": r.course_code,
            "rating": r.rating,
            "review_text": r.review_text,
            "is_anonymous": r.is_anonymous,
            "student_name": name
        })
    return result

@router.post("/{course_code}/reviews", response_model=schemas.CourseReviewResponse)
def create_course_review(course_code: int, student_id: int, review: schemas.CourseReviewCreate, db: Session = Depends(get_db)):
    if course_code != review.course_code:
        raise HTTPException(status_code=400, detail="Course code mismatch")
    r = crud.create_course_review(db, student_id, review)
    name = "Anonymous" if r.is_anonymous else (r.student.name if r.student else "Unknown")
    return {
        "id": r.id,
        "student_id": r.student_id,
        "course_code": r.course_code,
        "rating": r.rating,
        "review_text": r.review_text,
        "is_anonymous": r.is_anonymous,
        "student_name": name
    }

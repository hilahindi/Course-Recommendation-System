from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

import crud, schemas
from database import get_db

router = APIRouter(
    prefix="/api/profile",
    tags=["profile"]
)

@router.get("/{student_id}", response_model=schemas.StudentProfileResponse)
def read_profile(student_id: int, db: Session = Depends(get_db)):
    return crud.get_student_profile(db, student_id)

@router.put("/{student_id}", response_model=schemas.StudentProfileResponse)
def update_profile(student_id: int, profile_update: schemas.StudentProfileUpdate, db: Session = Depends(get_db)):
    return crud.update_student_profile(db, student_id, profile_update)

@router.get("/{student_id}/history", response_model=List[schemas.StudentCourseHistoryResponse])
def read_history(student_id: int, db: Session = Depends(get_db)):
    return crud.get_student_history(db, student_id)

@router.post("/{student_id}/history", response_model=schemas.StudentCourseHistoryResponse)
def add_history(student_id: int, history_create: schemas.StudentCourseHistoryCreate, db: Session = Depends(get_db)):
    return crud.add_student_course_history(db, student_id, history_create)

@router.post("/{student_id}/history/bulk", response_model=List[schemas.StudentCourseHistoryResponse])
def add_history_bulk(student_id: int, bulk_create: schemas.StudentCourseHistoryBulkCreate, db: Session = Depends(get_db)):
    return crud.add_student_course_history_bulk(db, student_id, bulk_create)

@router.get("/{student_id}/schedule", response_model=List[schemas.PlannedCourseResponse])
def get_schedule(student_id: int, db: Session = Depends(get_db)):
    return crud.get_planned_courses(db, student_id)

@router.post("/{student_id}/schedule", response_model=schemas.PlannedCourseResponse)
def add_schedule(student_id: int, course: schemas.PlannedCourseBase, db: Session = Depends(get_db)):
    return crud.add_planned_course(db, student_id, course.course_code)

@router.delete("/{student_id}/schedule/{course_code}")
def remove_schedule(student_id: int, course_code: int, db: Session = Depends(get_db)):
    crud.remove_planned_course(db, student_id, course_code)
    return {"status": "ok"}

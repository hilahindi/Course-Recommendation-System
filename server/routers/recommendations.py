from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

import schemas
from database import get_db
from services.recommendation import get_recommendations

router = APIRouter(
    prefix="/api/recommendations",
    tags=["recommendations"]
)

@router.get("/{student_id}", response_model=List[schemas.RecommendationResponse])
def read_recommendations(student_id: int, db: Session = Depends(get_db)):
    return get_recommendations(db, student_id)

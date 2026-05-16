from fastapi import APIRouter, Depends
from typing import List

from dependencies import get_recommendation_service
from dtos import RecommendationResponse
from interfaces.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("/{student_id}", response_model=List[RecommendationResponse])
def read_recommendations(
    student_id: int,
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    return recommendation_service.get_recommendations(student_id)

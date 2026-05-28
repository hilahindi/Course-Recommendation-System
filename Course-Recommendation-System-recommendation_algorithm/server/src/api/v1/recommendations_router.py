from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_student_id, get_recommendation_service
from interfaces.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post("/get", status_code=status.HTTP_200_OK)
async def get_personalized_recommendations(
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
) -> list[dict]:
    try:
        return await recommendation_service.get_personalized_recommendations(
            db, student_id
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {exc}",
        ) from exc

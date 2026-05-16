from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_course_repository
from repositories.course_repository import CourseRepository
from services.adzuna_sync_service import AdzunaSyncService

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post("/sync", status_code=status.HTTP_200_OK)
async def sync_market_trends(
    keyword: Optional[str] = None,
    repository: CourseRepository = Depends(get_course_repository),
) -> dict[str, str]:
    try:
        synced_count = await AdzunaSyncService(repository).sync_jobs(keyword=keyword)
        return {
            "status": "success",
            "message": (
                f"Successfully synchronized {synced_count} raw jobs from Adzuna API."
            ),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync jobs from Adzuna: {exc}",
        ) from exc

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])

# Adzuna sync moved to POST /api/v1/jobs/sync (job_listings pipeline).
# @router.post("/sync", status_code=status.HTTP_200_OK)
# async def sync_market_trends(
#     keyword: Optional[str] = None,
#     repository: CourseRepository = Depends(get_course_repository),
# ) -> dict[str, str]:
#     ...

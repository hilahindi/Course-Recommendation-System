from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_job_pipeline_service
from dtos import AverageFeatureVectorResponse
from interfaces.job_pipeline_service import JobPipelineService
from services.adzuna_sync_service_impl import AdzunaSyncServiceImpl

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("/sync", status_code=status.HTTP_200_OK)
async def sync_jobs_from_adzuna(
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    pipeline: JobPipelineService = Depends(get_job_pipeline_service),
) -> dict[str, str]:
    try:
        role_title = AdzunaSyncServiceImpl.resolve_search_what(keyword)
        synced_count = await pipeline.sync_from_adzuna(db, role_title)
        return {
            "status": "success",
            "message": (
                f"Successfully synchronized {synced_count} jobs into industry_jobs."
            ),
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync jobs from Adzuna: {exc}",
        ) from exc


@router.post("/extract-skills", status_code=status.HTTP_200_OK)
def extract_skills(
    db: Session = Depends(get_db),
    pipeline: JobPipelineService = Depends(get_job_pipeline_service),
) -> dict[str, str]:
    try:
        count = pipeline.extract_skills_from_listings(db)
        return {
            "status": "success",
            "message": f"Extracted skills for {count} row(s) in industry_jobs.extracted_skills.",
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Skill extraction failed: {exc}",
        ) from exc


@router.post("/vectorize-listings", status_code=status.HTTP_200_OK)
def vectorize_listings(
    db: Session = Depends(get_db),
    pipeline: JobPipelineService = Depends(get_job_pipeline_service),
) -> dict[str, str]:
    try:
        count = pipeline.vectorize_listings(db)
        return {
            "status": "success",
            "message": f"Vectorized {count} row(s) in industry_jobs.feature_vector.",
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Listing vectorization failed: {exc}",
        ) from exc


@router.get(
    "/average-vector",
    response_model=AverageFeatureVectorResponse,
    status_code=status.HTTP_200_OK,
)
def get_average_feature_vector(
    db: Session = Depends(get_db),
    pipeline: JobPipelineService = Depends(get_job_pipeline_service),
) -> AverageFeatureVectorResponse:
    try:
        result = pipeline.get_average_feature_vector(db)
        if not result["vector"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No feature vectors found. Run sync → extract-skills → "
                    "vectorize-listings first."
                ),
            )
        return AverageFeatureVectorResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute average vector: {exc}",
        ) from exc

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from database import get_db
from dependencies import get_course_repository, get_market_role_service
from dtos import JobRoleBase, TrackBase
from interfaces.market_role_service import MarketRoleService
from repositories.course_repository import CourseRepository

import config  # noqa: F401 — loads server/.env

router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])


def _serialize_job_roles(repository: CourseRepository) -> List[JobRoleBase]:
    return [JobRoleBase.model_validate(role) for role in repository.get_job_roles()]


@router.get("/", response_model=Dict[str, Any])
def read_metadata(
    repository: CourseRepository = Depends(get_course_repository),
    market_role_service: MarketRoleService = Depends(get_market_role_service),
    db: Session = Depends(get_db),
):
    try:
        repository.ensure_default_tracks()
        repository.ensure_track_course_links()
        tracks_db = repository.get_tracks()
        job_roles_db = repository.get_job_roles()

        if market_role_service.ensure_market_roles_in_db(db, len(job_roles_db)):
            job_roles_db = repository.get_job_roles()

        return {
            "tracks": [TrackBase.model_validate(t) for t in tracks_db],
            "job_roles": [JobRoleBase.model_validate(j) for j in job_roles_db],
        }
    except Exception as e:
        print(f"Error in GET /metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metadata")


@router.get("/market-roles", response_model=List[JobRoleBase])
def read_market_roles(
    repository: CourseRepository = Depends(get_course_repository),
    market_role_service: MarketRoleService = Depends(get_market_role_service),
    db: Session = Depends(get_db),
):
    try:
        market_role_service.ensure_market_roles_in_db(
            db, len(repository.get_job_roles())
        )
        return _serialize_job_roles(repository)
    except Exception as e:
        print(f"Error in GET /metadata/market-roles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market roles")


@router.post("/sync-market-roles")
def sync_market_roles_endpoint(
    market_role_service: MarketRoleService = Depends(get_market_role_service),
    db: Session = Depends(get_db),
):
    try:
        return market_role_service.sync_job_roles(db)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[Market Roles] Sync error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Market roles sync failed: {str(e)}"
        )

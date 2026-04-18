from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

import crud, schemas
from database import get_db

router = APIRouter(
    prefix="/api/metadata",
    tags=["metadata"]
)

@router.get("/", response_model=Dict[str, Any])
def read_metadata(db: Session = Depends(get_db)):
    tracks = crud.get_tracks(db)
    job_roles = crud.get_job_roles(db)
    return {
        "tracks": tracks,
        "job_roles": job_roles
    }

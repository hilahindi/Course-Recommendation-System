from functools import lru_cache

from fastapi import Depends, Header, HTTPException
from jose import JWTError
from sqlalchemy.orm import Session

import models
from auth import decode_access_token
from database import get_db
from interfaces.adzuna_sync_service import AdzunaSyncService
from interfaces.course_service import CourseService
from interfaces.embedding_service import EmbeddingService
from interfaces.job_pipeline_service import JobPipelineService
from interfaces.market_role_service import MarketRoleService
from interfaces.profile_service import ProfileService
from interfaces.recommendation_service import RecommendationService
from repositories.course_repository import CourseRepository
from services.adzuna_sync_service_impl import AdzunaSyncServiceImpl
from services.course_pipeline_service import (
    CoursePipelineService,
    CoursePipelineServiceImpl,
)
from services.course_service_impl import CourseServiceImpl
from services.embedding_service_impl import LocalEmbeddingServiceImpl
from services.job_pipeline_service_impl import JobPipelineServiceImpl
from services.market_role_service_impl import MarketRoleServiceImpl
from services.profile_service_impl import ProfileServiceImpl
from services.recommendation_service_impl import RecommendationServiceImpl
from services.roadmap_service_impl import RoadmapServiceImpl


def get_current_student_id(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        student_id = decode_access_token(token)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=401, detail="Invalid student credentials")
    return student_id


def verify_student_access(
    student_id: int,
    auth_id: int = Depends(get_current_student_id),
) -> int:
    """Ensure the authenticated student matches the student_id in the request path."""
    if student_id != auth_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access another student's data",
        )
    return student_id


def require_admin(
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db),
) -> int:
    """Allow only authenticated users whose role is 'admin'."""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student or student.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return student_id


def get_course_repository(db: Session = Depends(get_db)) -> CourseRepository:
    from catalog_sync import catalog_sync_status

    repository = CourseRepository(db)
    sync_status = catalog_sync_status().get("status")
    # Background sync owns the lock while running; retry only if it never ran or failed.
    if sync_status not in ("running", "ready", "skipped"):
        try:
            repository.ensure_catalog_synced()
        except Exception:
            db.rollback()
    return repository


def get_embedding_service() -> EmbeddingService:
    return _get_embedding_service_singleton()


@lru_cache
def _get_embedding_service_singleton() -> EmbeddingService:
    return LocalEmbeddingServiceImpl()


def get_course_pipeline_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> CoursePipelineService:
    return CoursePipelineServiceImpl(embedding_service)


def get_course_service(
    repository: CourseRepository = Depends(get_course_repository),
    pipeline: CoursePipelineService = Depends(get_course_pipeline_service),
) -> CourseService:
    return CourseServiceImpl(repository, pipeline)


def get_adzuna_sync_service() -> AdzunaSyncService:
    return AdzunaSyncServiceImpl()


def get_job_pipeline_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    adzuna_service: AdzunaSyncService = Depends(get_adzuna_sync_service),
) -> JobPipelineService:
    return JobPipelineServiceImpl(embedding_service, adzuna_service)


def get_recommendation_service(
    repository: CourseRepository = Depends(get_course_repository),
    job_pipeline: JobPipelineService = Depends(get_job_pipeline_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> RecommendationService:
    return RecommendationServiceImpl(repository, job_pipeline, embedding_service)


def get_market_role_service(
    repository: CourseRepository = Depends(get_course_repository),
) -> MarketRoleService:
    return MarketRoleServiceImpl(repository)


def get_profile_service(
    repository: CourseRepository = Depends(get_course_repository),
) -> ProfileService:
    return ProfileServiceImpl(repository)


def get_roadmap_service(
    repository: CourseRepository = Depends(get_course_repository),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
) -> RoadmapServiceImpl:
    return RoadmapServiceImpl(repository, recommendation_service)

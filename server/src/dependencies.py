from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

import models
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
    x_student_id: int = Header(..., alias="X-Student-Id"),
    db: Session = Depends(get_db),
) -> int:
    student = db.query(models.Student).filter(models.Student.id == x_student_id).first()
    if not student:
        raise HTTPException(status_code=401, detail="Invalid or missing student credentials")
    return x_student_id


def get_course_repository(db: Session = Depends(get_db)) -> CourseRepository:
    return CourseRepository(db)


def get_embedding_service() -> EmbeddingService:
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
) -> RoadmapServiceImpl:
    return RoadmapServiceImpl(repository)

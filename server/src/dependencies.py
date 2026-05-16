from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from interfaces.course_service import CourseService
from interfaces.market_role_service import MarketRoleService
from interfaces.profile_service import ProfileService
from interfaces.recommendation_service import RecommendationService
from repositories.course_repository import CourseRepository
from services.course_service_impl import CourseServiceImpl
from services.market_role_service_impl import MarketRoleServiceImpl
from services.profile_service_impl import ProfileServiceImpl
from services.recommendation_service_impl import RecommendationServiceImpl


def get_course_repository(db: Session = Depends(get_db)) -> CourseRepository:
    return CourseRepository(db)


def get_course_service(
    repository: CourseRepository = Depends(get_course_repository),
) -> CourseService:
    return CourseServiceImpl(repository)


def get_recommendation_service(
    repository: CourseRepository = Depends(get_course_repository),
) -> RecommendationService:
    return RecommendationServiceImpl(repository)


def get_market_role_service(
    repository: CourseRepository = Depends(get_course_repository),
) -> MarketRoleService:
    return MarketRoleServiceImpl(repository)


def get_profile_service(
    repository: CourseRepository = Depends(get_course_repository),
) -> ProfileService:
    return ProfileServiceImpl(repository)

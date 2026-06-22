import os

from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from api.v1 import (
    admin_router,
    auth_router,
    courses_router,
    jobs_router,
    metadata_router,
    profile_router,
    recommendations_router,
)
from catalog_sync import bootstrap_catalog_sync, catalog_sync_status
from database import (
    SessionLocal,
    engine,
    drop_jobrole_skill_link_table,
    drop_jobroles_skill_vector,
    ensure_courses_table_sync,
    ensure_industry_jobs_table_sync,
    ensure_students_table_sync,
)
from repositories.course_repository import CourseRepository
from services.market_role_service_impl import MarketRoleServiceImpl

models.Base.metadata.create_all(bind=engine)
ensure_courses_table_sync()
ensure_industry_jobs_table_sync()
ensure_students_table_sync()
drop_jobroles_skill_vector()
drop_jobrole_skill_link_table()

scheduler = BackgroundScheduler()


def scheduled_market_sync():
    print("⏰ [Cron Job] Starting automated market roles sync...")
    db = SessionLocal()
    try:
        market_role_service = MarketRoleServiceImpl(CourseRepository(db))
        result = market_role_service.sync_job_roles(db)
        print(f"✅ [Cron Job] Sync completed: {result['message']}")
    except Exception as e:
        print(f"❌ [Cron Job] Critical error during sync: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_catalog_sync()
    scheduler.add_job(scheduled_market_sync, "cron", day_of_week="sun", hour=1, minute=0)
    scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)

_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(courses_router.router)
app.include_router(courses_router.reviews_router)
app.include_router(courses_router.course_pipeline_router)
app.include_router(profile_router.router)
app.include_router(recommendations_router.router)
app.include_router(metadata_router.router)
app.include_router(jobs_router.router)
app.include_router(admin_router.router)


@app.get("/api/v1/test")
def read_test():
    sync = catalog_sync_status()
    return {
        "status": "success",
        "message": "The server is connected to the client and Cron Job is active!",
        "catalog_sync": sync,
    }

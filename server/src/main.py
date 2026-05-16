from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from api.v1.routes import auth, courses, metadata, profile, recommendations
from database import SessionLocal, engine
from api.v1.routes.metadata import sync_job_roles_from_ai

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def scheduled_market_sync():
    print("⏰ [Cron Job] Starting automated market roles sync...")
    db = SessionLocal()
    try:
        result = sync_job_roles_from_ai(db)
        print(f"✅ [Cron Job] Sync completed: {result['message']}")
    except Exception as e:
        print(f"❌ [Cron Job] Critical error during sync: {e}")
    finally:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_market_sync, "cron", day_of_week="sun", hour=1, minute=0)
scheduler.start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(profile.router)
app.include_router(recommendations.router)
app.include_router(metadata.router)


@app.get("/api/v1/test")
def read_test():
    return {
        "status": "success",
        "message": "The server is connected to the client and Cron Job is active!",
    }

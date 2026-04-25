from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import bcrypt
import logging

# ייבוא עבור ה-Cron Job
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal

import models
from database import engine, get_db
from routers import courses, profile, recommendations, metadata

# יצירת הטבלאות
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- הגדרת ה-Cron Job (משימות רקע) ---

def scheduled_market_sync():
    """פונקציה שרצה ברקע ומעדכנת את המשרות דרך ה-AI"""
    print("⏰ [Cron Job] Starting automated market roles sync...")
    db = SessionLocal()
    try:
        # אנחנו קוראים ישירות לפונקציה מהראוטר כדי לא לשכפל קוד
        from routers.metadata import sync_job_roles_from_ai
        result = sync_job_roles_from_ai(db)
        print(f"✅ [Cron Job] Sync completed: {result['message']}")
    except Exception as e:
        print(f"❌ [Cron Job] Critical error during sync: {e}")
    finally:
        db.close()

# אתחול המתזמן
scheduler = BackgroundScheduler()

# הגדרה לריצה כל יום ראשון ב-01:00 בלילה
# בזמן פיתוח אפשר לשנות ל minutes=5 כדי לראות שזה עובד
scheduler.add_job(scheduled_market_sync, 'cron', day_of_week='sun', hour=1, minute=0)
scheduler.start()

# ------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

@app.post("/api/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Student).filter(models.Student.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user.password)
    new_student = models.Student(email=user.email, name=user.name, hashed_password=hashed_password)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    new_profile = models.StudentProfile(student_id=new_student.id)
    db.add(new_profile)
    db.commit()
    
    return {"message": "User registered successfully"}

@app.post("/api/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.Student).filter(models.Student.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    return {"message": "Login successful", "user_id": db_user.id, "name": db_user.name}

# הכללת הראוטרים
app.include_router(courses.router)
app.include_router(profile.router)
app.include_router(recommendations.router)
app.include_router(metadata.router)

@app.get("/api/test")   
def read_test():
    return {"status": "success", "message": "The server is connected to the client and Cron Job is active!"}
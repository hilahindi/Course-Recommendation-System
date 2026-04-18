from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import bcrypt

import models
from database import engine, get_db
from routers import courses, profile, recommendations, metadata

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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
    
    # Create empty profile
    new_profile = models.StudentProfile(student_id=new_student.id)
    db.add(new_profile)
    db.commit()
    
    return {"message": "User registered successfully"}

@app.post("/api/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.Student).filter(models.Student.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # Normally we would return a JWT token here. For phase 1, just returning user info
    return {"message": "Login successful", "user_id": db_user.id, "name": db_user.name}

app.include_router(courses.router)
app.include_router(profile.router)
app.include_router(recommendations.router)
app.include_router(metadata.router)

@app.get("/api/test")   
def read_test():
    return {"status": "success", "message": "The server is connected to the client!"}

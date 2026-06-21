from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import bcrypt

import models
from auth import create_access_token
from database import get_db

router = APIRouter(prefix="/api/v1", tags=["auth"])


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Student).filter(models.Student.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_student = models.Student(
        email=user.email,
        name=user.name,
        hashed_password=hash_password(user.password),
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    db.add(models.StudentProfile(student_id=new_student.id))
    db.commit()

    return {"message": "User registered successfully"}


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.Student).filter(models.Student.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    return {
        "message": "Login successful",
        "access_token": create_access_token(db_user.id),
        "token_type": "bearer",
        "user_id": db_user.id,
        "name": db_user.name,
    }

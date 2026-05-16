import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import config  # noqa: F401 — loads server/.env

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:password123@127.0.0.1:5433/course_recommender",
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

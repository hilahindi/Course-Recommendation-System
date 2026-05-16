import os

from sqlalchemy import create_engine, inspect
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


_INDUSTRY_JOBS_TABLE = "industry_jobs"
_INDUSTRY_JOBS_COLUMNS = frozenset({"id", "title", "description", "updated_at"})


def ensure_industry_jobs_table_sync() -> None:
    import models

    inspector = inspect(engine)
    if _INDUSTRY_JOBS_TABLE not in inspector.get_table_names():
        models.IndustryJob.__table__.create(bind=engine)
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns(_INDUSTRY_JOBS_TABLE)
    }
    missing = _INDUSTRY_JOBS_COLUMNS - existing_columns
    if missing:
        raise RuntimeError(
            f"{_INDUSTRY_JOBS_TABLE} is missing columns: {', '.join(sorted(missing))}."
        )

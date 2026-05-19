import os

from sqlalchemy import create_engine, inspect, text
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
_INDUSTRY_JOBS_REQUIRED_COLUMNS = frozenset(
    {
        "id",
        "title",
        "description",
        "updated_at",
        "extracted_skills",
        "feature_vector",
    }
)
_INDUSTRY_JOBS_COLUMN_ALTER = {
    "extracted_skills": (
        "ALTER TABLE industry_jobs ADD COLUMN IF NOT EXISTS extracted_skills TEXT"
    ),
    "feature_vector": (
        "ALTER TABLE industry_jobs ADD COLUMN IF NOT EXISTS feature_vector JSONB"
    ),
}


def ensure_industry_jobs_table_sync() -> None:
    import models

    inspector = inspect(engine)
    if _INDUSTRY_JOBS_TABLE not in inspector.get_table_names():
        models.IndustryJob.__table__.create(bind=engine)
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns(_INDUSTRY_JOBS_TABLE)
    }
    missing = _INDUSTRY_JOBS_REQUIRED_COLUMNS - existing_columns
    if not missing:
        return

    with engine.begin() as conn:
        for column_name in sorted(missing):
            if column_name in _INDUSTRY_JOBS_COLUMN_ALTER:
                conn.execute(text(_INDUSTRY_JOBS_COLUMN_ALTER[column_name]))
            elif column_name not in existing_columns:
                raise RuntimeError(
                    f"{_INDUSTRY_JOBS_TABLE} is missing column '{column_name}' "
                    "and has no automatic alter defined."
                )


def drop_jobroles_skill_vector() -> None:
    """Remove obsolete skill_vector column from jobroles if it still exists."""
    inspector = inspect(engine)
    if "jobroles" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("jobroles")}
    if "skill_vector" not in column_names:
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE jobroles DROP COLUMN skill_vector"))


_COURSES_COLUMN_ALTER = {
    "avg_rating": (
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS "
        "avg_rating DOUBLE PRECISION NOT NULL DEFAULT 0.0"
    ),
    "skills": "ALTER TABLE courses ADD COLUMN IF NOT EXISTS skills TEXT",
    "feature_vector": (
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS feature_vector JSONB"
    ),
}


def ensure_courses_table_sync() -> None:
    """Add columns introduced on the Course model to existing databases."""
    inspector = inspect(engine)
    if "courses" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("courses")}
    missing = set(_COURSES_COLUMN_ALTER) - column_names
    if not missing:
        return

    with engine.begin() as conn:
        for column_name in sorted(missing):
            conn.execute(text(_COURSES_COLUMN_ALTER[column_name]))


def drop_jobrole_skill_link_table() -> None:
    """Remove obsolete many-to-many table between jobroles and skills."""
    inspector = inspect(engine)
    if "jobrole_skill_link" not in inspector.get_table_names():
        return

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE jobrole_skill_link"))

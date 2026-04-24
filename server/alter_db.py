from sqlalchemy import text
from database import SessionLocal, engine
import models

db = SessionLocal()

# Create planned_courses table if it doesn't exist
models.Base.metadata.create_all(bind=engine)

queries = [
    "ALTER TABLE courses ADD COLUMN day_of_week VARCHAR;",
    "ALTER TABLE courses ADD COLUMN start_time VARCHAR;",
    "ALTER TABLE courses ADD COLUMN end_time VARCHAR;",
    "ALTER TABLE courses ADD COLUMN room VARCHAR;",
    "ALTER TABLE courses ADD COLUMN lecturer VARCHAR;",
    "ALTER TABLE course_reviews ADD COLUMN is_anonymous BOOLEAN DEFAULT FALSE;"
]

for q in queries:
    try:
        db.execute(text(q))
        db.commit()
    except Exception as e:
        print(f"Skipping (might already exist): {e}")
        db.rollback()

db.close()
print("Database schema updated.")

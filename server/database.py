from sqlalchemy import create_all, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL connection string
# format: postgresql://user:password@localhost:port/dbname
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost:5432/course_recommender"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
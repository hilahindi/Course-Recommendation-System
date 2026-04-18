from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
import models, schemas

def get_courses(db: Session):
    return db.query(models.Course).all()

def get_tracks(db: Session):
    return db.query(models.Track).all()

def get_job_roles(db: Session):
    return db.query(models.JobRole).all()

def get_student_profile(db: Session, student_id: int):
    profile = db.query(models.StudentProfile).filter(models.StudentProfile.student_id == student_id).first()
    if not profile:
        profile = models.StudentProfile(student_id=student_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def update_student_profile(db: Session, student_id: int, profile_update: schemas.StudentProfileUpdate):
    profile = get_student_profile(db, student_id)
    
    profile.target_workload = profile_update.target_workload
    profile.needs_flexible_attendance = profile_update.needs_flexible_attendance
    if profile_update.degree is not None:
        profile.degree = profile_update.degree
    if profile_update.year_of_study is not None:
        profile.year_of_study = profile_update.year_of_study
    if profile_update.available_days is not None:
        profile.available_days = profile_update.available_days
    if profile_update.onboarding_completed is not None:
        profile.onboarding_completed = profile_update.onboarding_completed
    
    # Update Many-to-Many relationships
    profile.interested_tracks = db.query(models.Track).filter(models.Track.id.in_(profile_update.interested_track_ids)).all()
    profile.interested_job_roles = db.query(models.JobRole).filter(models.JobRole.id.in_(profile_update.interested_job_role_ids)).all()
    
    db.commit()
    db.refresh(profile)
    return profile

def get_student_history(db: Session, student_id: int):
    return db.query(models.StudentCourseHistory).filter(models.StudentCourseHistory.student_id == student_id).all()

def add_student_course_history(db: Session, student_id: int, history_create: schemas.StudentCourseHistoryCreate):
    # Check if already exists to avoid duplicates
    existing = db.query(models.StudentCourseHistory).filter_by(student_id=student_id, course_code=history_create.course_code).first()
    if existing:
        existing.grade = history_create.grade
        db.commit()
        db.refresh(existing)
        return existing

    history = models.StudentCourseHistory(
        student_id=student_id,
        course_code=history_create.course_code,
        grade=history_create.grade
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def add_student_course_history_bulk(db: Session, student_id: int, bulk_create: schemas.StudentCourseHistoryBulkCreate):
    added_histories = []
    for course_data in bulk_create.courses:
        # Check if already exists
        existing = db.query(models.StudentCourseHistory).filter_by(student_id=student_id, course_code=course_data.course_code).first()
        if existing:
            existing.grade = course_data.grade
            added_histories.append(existing)
        else:
            history = models.StudentCourseHistory(
                student_id=student_id,
                course_code=course_data.course_code,
                grade=course_data.grade
            )
            db.add(history)
            added_histories.append(history)
    
    db.commit()
    for h in added_histories:
        db.refresh(h)
    return added_histories

def get_course_reviews(db: Session, course_code: int):
    return db.query(models.CourseReview).filter(models.CourseReview.course_code == course_code).all()

def create_course_review(db: Session, student_id: int, review: schemas.CourseReviewCreate):
    existing = db.query(models.CourseReview).filter_by(student_id=student_id, course_code=review.course_code).first()
    if existing:
        existing.rating = review.rating
        existing.review_text = review.review_text
        db.commit()
        db.refresh(existing)
        return existing
    
    db_review = models.CourseReview(
        student_id=student_id,
        course_code=review.course_code,
        rating=review.rating,
        review_text=review.review_text
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


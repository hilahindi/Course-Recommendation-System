import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

import models
from dtos import (
    CourseOccurrenceSchema,
    CourseReviewCreate,
    StudentCourseHistoryBulkCreate,
    StudentCourseHistoryCreate,
    StudentProfileUpdate,
)


class CourseRepository:
    """Relational database access for courses and related entities."""

    def __init__(self, db: Session):
        self._db = db

    # --- Courses ---

    def get_courses(self) -> List[models.Course]:
        return self._db.query(models.Course).all()

    def get_courses_by_categories(self, categories: List[str]) -> List[models.Course]:
        return (
            self._db.query(models.Course)
            .filter(models.Course.category.in_(categories))
            .all()
        )

    def get_yearly_mandatory_map(self) -> dict[int, list[int]]:
        mandatory_categories = ["year-A", "year-B", "year-C"]
        courses = self.get_courses_by_categories(mandatory_categories)
        category_to_year = {"year-A": 1, "year-B": 2, "year-C": 3}
        yearly_map: dict[int, list[int]] = defaultdict(list)
        for course in courses:
            year = category_to_year.get(course.category)
            if year:
                yearly_map[year].append(course.course_code)
        return dict(yearly_map)

    def get_course_reviews(self, course_code: int) -> List[models.CourseReview]:
        return (
            self._db.query(models.CourseReview)
            .filter(models.CourseReview.course_code == course_code)
            .all()
        )

    def get_course_by_code(self, course_code: int) -> Optional[models.Course]:
        return (
            self._db.query(models.Course)
            .filter(models.Course.course_code == course_code)
            .first()
        )

    def get_courses_for_pipeline(self) -> List[models.Course]:
        return self._db.query(models.Course).all()

    def get_courses_with_empty_skills(self) -> List[models.Course]:
        return (
            self._db.query(models.Course)
            .filter(
                (models.Course.skills.is_(None))
                | (models.Course.skills == "")
            )
            .all()
        )

    def bulk_update_course_skills(
        self, assignments: list[tuple[models.Course, str]]
    ) -> int:
        for course, skills in assignments:
            course.skills = skills
        if assignments:
            self._db.commit()
        return len(assignments)

    def get_courses_with_skills_text(self) -> List[models.Course]:
        return (
            self._db.query(models.Course)
            .filter(
                models.Course.skills.isnot(None),
                models.Course.skills != "",
            )
            .all()
        )

    def get_student_by_email(self, email: str) -> Optional[models.Student]:
        return (
            self._db.query(models.Student)
            .filter(models.Student.email == email)
            .first()
        )

    def create_seed_student(
        self, email: str, name: str, hashed_password: str
    ) -> models.Student:
        student = models.Student(
            email=email, name=name, hashed_password=hashed_password
        )
        self._db.add(student)
        self._db.flush()
        self._db.add(models.StudentProfile(student_id=student.id))
        self._db.commit()
        self._db.refresh(student)
        return student

    def upsert_seed_course(
        self,
        course_code: int,
        name: str,
        workload: int = 6,
        category: str = "elective",
    ) -> tuple[models.Course, bool]:
        existing = self.get_course_by_code(course_code)
        if existing:
            return existing, False

        course = models.Course(
            course_code=course_code,
            name=name,
            workload=workload,
            category=category,
            avg_rating=0.0,
        )
        self._db.add(course)
        self._db.commit()
        self._db.refresh(course)
        return course, True

    def add_seed_review(
        self,
        student_id: int,
        course_code: int,
        rating: int,
        review_text: str,
        is_anonymous: bool = False,
    ) -> models.CourseReview:
        return self.create_course_review(
            student_id,
            CourseReviewCreate(
                course_code=course_code,
                rating=rating,
                review_text=review_text,
                is_anonymous=is_anonymous,
            ),
        )

    def update_course_skills(self, course: models.Course, skills: str) -> None:
        course.skills = skills
        self._db.commit()

    def update_course_feature_vector(
        self, course: models.Course, vector: list[float]
    ) -> None:
        course.feature_vector = vector
        self._db.commit()

    def update_course_avg_rating(self, course_code: int, avg_rating: float) -> None:
        course = self.get_course_by_code(course_code)
        if course:
            course.avg_rating = avg_rating
            self._db.commit()

    def get_average_ratings_by_course(self) -> dict[int, float]:
        rows = (
            self._db.query(
                models.CourseReview.course_code,
                func.avg(models.CourseReview.rating),
            )
            .group_by(models.CourseReview.course_code)
            .all()
        )
        return {int(course_code): float(avg) for course_code, avg in rows}

    def create_course_review(
        self, student_id: int, review: CourseReviewCreate
    ) -> models.CourseReview:
        existing = (
            self._db.query(models.CourseReview)
            .filter_by(student_id=student_id, course_code=review.course_code)
            .first()
        )
        if existing:
            existing.rating = review.rating
            existing.review_text = review.review_text
            existing.is_anonymous = review.is_anonymous
            self._db.commit()
            self._db.refresh(existing)
            return existing

        db_review = models.CourseReview(
            student_id=student_id,
            course_code=review.course_code,
            rating=review.rating,
            review_text=review.review_text,
            is_anonymous=review.is_anonymous,
        )
        self._db.add(db_review)
        self._db.commit()
        self._db.refresh(db_review)
        return db_review

    def add_course_occurrence(
        self, course_code: int, occurrence: CourseOccurrenceSchema
    ) -> models.CourseOccurrence:
        db_occurrence = models.CourseOccurrence(
            course_code=course_code,
            day_of_week=occurrence.day_of_week,
            start_time=occurrence.start_time,
            end_time=occurrence.end_time,
            room=occurrence.room,
            lecturer=occurrence.lecturer,
            occurrence_type=occurrence.occurrence_type,
        )
        self._db.add(db_occurrence)
        self._db.commit()
        self._db.refresh(db_occurrence)
        return db_occurrence

    def add_course_prerequisite(
        self, course_code: int, prerequisite_code: int
    ) -> Optional[models.Course]:
        course = (
            self._db.query(models.Course)
            .filter(models.Course.course_code == course_code)
            .first()
        )
        prereq = (
            self._db.query(models.Course)
            .filter(models.Course.course_code == prerequisite_code)
            .first()
        )
        if course and prereq and prereq not in course.prerequisite_courses:
            course.prerequisite_courses.append(prereq)
            self._db.commit()
            self._db.refresh(course)
        return course

    # --- Metadata ---

    _DEFAULT_TRACK_NAMES: tuple[str, ...] = (
        "Web Development",
        "Cyber Security",
        "Data Science",
    )

    def ensure_default_tracks(self) -> None:
        """Insert default tracks when the table is empty (e.g. after partial seed)."""
        existing_names = {track.name for track in self.get_tracks()}
        added = False
        for name in self._DEFAULT_TRACK_NAMES:
            if name not in existing_names:
                self._db.add(models.Track(name=name))
                added = True
        if added:
            self._db.commit()

    def get_tracks(self) -> List[models.Track]:
        return self._db.query(models.Track).all()

    def get_job_roles(self) -> List[models.JobRole]:
        return self._db.query(models.JobRole).all()

    # --- Student profile & history ---

    def get_student_profile(self, student_id: int) -> models.StudentProfile:
        profile = (
            self._db.query(models.StudentProfile)
            .filter(models.StudentProfile.student_id == student_id)
            .first()
        )
        if not profile:
            profile = models.StudentProfile(student_id=student_id)
            self._db.add(profile)
            self._db.commit()
            self._db.refresh(profile)
        return profile

    def update_student_profile(
        self, student_id: int, profile_update: StudentProfileUpdate
    ) -> models.StudentProfile:
        profile = self.get_student_profile(student_id)

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

        if profile_update.availabilities is not None:
            self._db.query(models.StudentAvailability).filter(
                models.StudentAvailability.profile_id == profile.id
            ).delete()
            for avail in profile_update.availabilities:
                self._db.add(
                    models.StudentAvailability(
                        profile_id=profile.id,
                        day_of_week=avail.day_of_week,
                        start_time=avail.start_time,
                        end_time=avail.end_time,
                    )
                )

        profile.interested_tracks = (
            self._db.query(models.Track)
            .filter(models.Track.id.in_(profile_update.interested_track_ids))
            .all()
        )
        profile.interested_job_roles = (
            self._db.query(models.JobRole)
            .filter(models.JobRole.id.in_(profile_update.interested_job_role_ids))
            .all()
        )

        self._db.commit()
        self._db.refresh(profile)
        return profile

    def get_student_history(self, student_id: int) -> List[models.StudentCourseHistory]:
        return (
            self._db.query(models.StudentCourseHistory)
            .filter(models.StudentCourseHistory.student_id == student_id)
            .all()
        )

    def add_student_course_history(
        self, student_id: int, history_create: StudentCourseHistoryCreate
    ) -> models.StudentCourseHistory:
        existing = (
            self._db.query(models.StudentCourseHistory)
            .filter_by(student_id=student_id, course_code=history_create.course_code)
            .first()
        )
        if existing:
            existing.grade = history_create.grade
            self._db.commit()
            self._db.refresh(existing)
            return existing

        history = models.StudentCourseHistory(
            student_id=student_id,
            course_code=history_create.course_code,
            grade=history_create.grade,
        )
        self._db.add(history)
        self._db.commit()
        self._db.refresh(history)
        return history

    def add_student_course_history_bulk(
        self, student_id: int, bulk_create: StudentCourseHistoryBulkCreate
    ) -> List[models.StudentCourseHistory]:
        added_histories: List[models.StudentCourseHistory] = []
        for course_data in bulk_create.courses:
            existing = (
                self._db.query(models.StudentCourseHistory)
                .filter_by(student_id=student_id, course_code=course_data.course_code)
                .first()
            )
            if existing:
                existing.grade = course_data.grade
                added_histories.append(existing)
            else:
                history = models.StudentCourseHistory(
                    student_id=student_id,
                    course_code=course_data.course_code,
                    grade=course_data.grade,
                )
                self._db.add(history)
                added_histories.append(history)

        self._db.commit()
        for history in added_histories:
            self._db.refresh(history)
        return added_histories

    def get_planned_courses(self, student_id: int) -> List[models.PlannedCourse]:
        return (
            self._db.query(models.PlannedCourse)
            .filter(models.PlannedCourse.student_id == student_id)
            .all()
        )

    def add_planned_course(
        self, student_id: int, course_code: int
    ) -> models.PlannedCourse:
        existing = (
            self._db.query(models.PlannedCourse)
            .filter_by(student_id=student_id, course_code=course_code)
            .first()
        )
        if not existing:
            planned = models.PlannedCourse(
                student_id=student_id, course_code=course_code
            )
            self._db.add(planned)
            self._db.commit()
            self._db.refresh(planned)
            return planned
        return existing

    def remove_planned_course(self, student_id: int, course_code: int) -> bool:
        existing = (
            self._db.query(models.PlannedCourse)
            .filter_by(student_id=student_id, course_code=course_code)
            .first()
        )
        if existing:
            self._db.delete(existing)
            self._db.commit()
        return True

    # --- Industry jobs (Adzuna sync) ---

    async def bulk_update_industry_jobs(self, jobs: list[dict]) -> None:
        await asyncio.to_thread(self._bulk_update_industry_jobs_sync, jobs)

    def _bulk_update_industry_jobs_sync(self, jobs: list[dict]) -> None:
        if not jobs:
            return

        now = datetime.now(timezone.utc)
        rows = [
            {
                "id": str(job["id"]),
                "title": job["title"],
                "description": job["description"],
                "updated_at": now,
            }
            for job in jobs
        ]

        stmt = insert(models.IndustryJob).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        try:
            self._db.execute(stmt)
            current_ids = [str(job["id"]) for job in jobs]
            (
                self._db.query(models.IndustryJob)
                .filter(models.IndustryJob.id.notin_(current_ids))
                .delete(synchronize_session=False)
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

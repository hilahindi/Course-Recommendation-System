from collections import defaultdict
from typing import List, Optional

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

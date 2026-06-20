"""Academic course data pipeline — seed, skill extraction, vectorization, ratings."""

from __future__ import annotations

from abc import ABC, abstractmethod

import bcrypt
import numpy as np
from sqlalchemy.orm import Session

from dtos import CourseReviewCreate
from interfaces.embedding_service import EmbeddingService
from repositories.course_repository import CourseRepository
from services.course_skills_catalog import resolve_skills_from_course_title

SEED_STUDENT_EMAILS: tuple[tuple[str, str], ...] = (
    ("pipeline.reviewer1@seed.local", "user1"),
    ("pipeline.reviewer2@seed.local", "user2"),
    ("pipeline.reviewer3@seed.local", "user3"),
)

DEMO_REVIEW_TEMPLATES: tuple[tuple[str, int, bool], ...] = (
    ("קורס מעניין עם תוכן רלוונטי לתואר.", 4, False),
    ("המרצה מסביר ברור, העומס סביר.", 5, False),
    ("עבודות מעשיות שעזרו להבין את החומר לעומק.", 4, True),
    ("חומר מעמיק — דורש השקעה מחוץ לכיתה.", 3, True),
    ("תרגולים מומלצים, המבחן היה הוגן.", 5, False),
    ("קצת יבש בהרצאות, אבל החומר שימושי.", 3, False),
    ("אחד הקורסים הכי טובים שלקחתי.", 5, False),
    ("הרבה מטלות, קשה לעמוד בלוח הזמנים.", 2, True),
    ("למדתי הרבה, במיוחד מהפרויקט בסוף.", 4, False),
    ("מרצה נגיש ומסביר שוב כשלא מבינים.", 5, True),
    ("המעבדות היו מצוינות ומלמדות.", 4, False),
    ("ציפיתי ליותר תוכן מעשי.", 3, True),
    ("שילוב טוב בין תיאוריה לתרגול.", 4, False),
    ("קורס חובה — לא אהבתי אבל עברתי.", 3, True),
    ("עזר לי מאוד בהשמה לעבודה.", 5, False),
    ("ההרצאות ארוכות, קשה להישאר מרוכז.", 2, True),
    ("חומר מעודכן ורלוונטי לשוק.", 4, False),
    ("הקבוצה קטנה, אווירה נעימה.", 5, False),
)

SEED_COURSES: tuple[dict, ...] = (
    {
        "course_code": 10401,
        "name": "Data Structures and Algorithms",
        "workload": 8,
        "reviews": (
            {
                "student_index": 0,
                "rating": 5,
                "review_text": "Excellent foundation for technical interviews and problem solving.",
                "is_anonymous": False,
            },
            {
                "student_index": 1,
                "rating": 4,
                "review_text": "Challenging but fair; weekly assignments take time.",
                "is_anonymous": True,
            },
            {
                "student_index": 2,
                "rating": 3,
                "review_text": "Useful content, though lectures move quickly.",
                "is_anonymous": False,
            },
        ),
    },
    {
        "course_code": 10402,
        "name": "Advanced Web Development",
        "workload": 6,
        "reviews": (
            {
                "student_index": 0,
                "rating": 5,
                "review_text": "Great hands-on projects with React and a modern API stack.",
                "is_anonymous": False,
            },
            {
                "student_index": 1,
                "rating": 4,
                "review_text": "Practical course; team project was the highlight.",
                "is_anonymous": False,
            },
        ),
    },
    {
        "course_code": 10403,
        "name": "Database Systems",
        "workload": 5,
        "reviews": (
            {
                "student_index": 0,
                "rating": 4,
                "review_text": "Solid coverage of SQL and relational design principles.",
                "is_anonymous": True,
            },
            {
                "student_index": 2,
                "rating": 2,
                "review_text": "Labs were helpful but the midterm felt disproportionately hard.",
                "is_anonymous": True,
            },
            {
                "student_index": 1,
                "rating": 5,
                "review_text": "Best explanation of normalization and indexing I have had.",
                "is_anonymous": False,
            },
        ),
    },
    {
        "course_code": 10404,
        "name": "Introduction to Cybersecurity",
        "workload": 5,
        "reviews": (
            {
                "student_index": 1,
                "rating": 4,
                "review_text": "Engaging intro to threats, defenses, and network security basics.",
                "is_anonymous": False,
            },
            {
                "student_index": 2,
                "rating": 3,
                "review_text": "Interesting topics; wanted more lab time on penetration testing.",
                "is_anonymous": True,
            },
        ),
    },
    {
        "course_code": 10405,
        "name": "Cloud Architecture",
        "workload": 6,
        "reviews": (
            {
                "student_index": 0,
                "rating": 5,
                "review_text": "Clear overview of cloud patterns, scaling, and deployment trade-offs.",
                "is_anonymous": False,
            },
            {
                "student_index": 2,
                "rating": 4,
                "review_text": "Good mix of theory and architecture diagrams; labs were concise.",
                "is_anonymous": False,
            },
            {
                "student_index": 1,
                "rating": 1,
                "review_text": "Pace was too fast for students new to distributed systems.",
                "is_anonymous": True,
            },
        ),
    },
    {
        "course_code": 10406,
        "name": "Software Engineering Principles",
        "workload": 4,
        "reviews": (
            {
                "student_index": 0,
                "rating": 4,
                "review_text": "Useful focus on design patterns, testing, and team workflows.",
                "is_anonymous": False,
            },
            {
                "student_index": 1,
                "rating": 3,
                "review_text": "Concepts are valuable; some sessions felt repetitive.",
                "is_anonymous": True,
            },
        ),
    },
)

class CoursePipelineService(ABC):
    """Contract for the academic course data pipeline."""

    @abstractmethod
    def seed_initial_courses_and_reviews(self, db_session: Session) -> dict:
        ...

    @abstractmethod
    def extract_course_skills(self, db_session: Session) -> int:
        ...

    @abstractmethod
    def vectorize_courses(self, db_session: Session) -> int:
        ...

    @abstractmethod
    def compile_course_ratings(self, db_session: Session) -> int:
        ...

    @abstractmethod
    def seed_reviews_for_all_courses(self, db_session: Session) -> dict:
        ...


class CoursePipelineServiceImpl(CoursePipelineService):
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self._embedding_service = embedding_service

    def seed_initial_courses_and_reviews(self, db_session: Session) -> dict:
        repository = CourseRepository(db_session)
        courses_inserted = 0
        reviews_inserted = 0
        students_inserted = 0

        student_ids, students_inserted = self._ensure_seed_students(repository)

        for course_data in SEED_COURSES:
            _, created = repository.upsert_seed_course(
                course_code=course_data["course_code"],
                name=course_data["name"],
                workload=course_data["workload"],
            )
            if created:
                courses_inserted += 1

            for review_data in course_data["reviews"]:
                student_id = student_ids[review_data["student_index"]]
                repository.add_seed_review(
                    student_id=student_id,
                    course_code=course_data["course_code"],
                    rating=review_data["rating"],
                    review_text=review_data["review_text"],
                    is_anonymous=review_data.get("is_anonymous", False),
                )
                reviews_inserted += 1

        return {
            "status": "success",
            "courses_inserted": courses_inserted,
            "reviews_inserted": reviews_inserted,
            "students_inserted": students_inserted,
            "message": (
                f"Seeded {courses_inserted} course(s), {reviews_inserted} review(s), "
                f"and {students_inserted} student(s)."
            ),
        }

    def _ensure_seed_students(
        self, repository: CourseRepository
    ) -> tuple[list[int], int]:
        seed_password = bcrypt.hashpw(
            b"pipeline-seed", bcrypt.gensalt()
        ).decode("utf-8")

        student_ids: list[int] = []
        students_inserted = 0
        names_updated = False

        for email, name in SEED_STUDENT_EMAILS:
            existing = repository.get_student_by_email(email)
            if existing:
                if existing.name != name:
                    existing.name = name
                    names_updated = True
                student_ids.append(existing.id)
                continue
            student = repository.create_seed_student(email, name, seed_password)
            student_ids.append(student.id)
            students_inserted += 1

        if names_updated:
            repository.commit()

        return student_ids, students_inserted

    def seed_reviews_for_all_courses(self, db_session: Session) -> dict:
        repository = CourseRepository(db_session)
        student_ids, _ = self._ensure_seed_students(repository)
        courses = repository.get_courses_for_pipeline()

        if not courses:
            return {
                "status": "success",
                "reviews_inserted": 0,
                "courses_seeded": 0,
                "invalid_course_codes": [],
                "message": "No courses found in the database.",
            }

        pending: list[tuple[int, CourseReviewCreate]] = []
        updated_course_codes: set[int] = set()
        template_count = len(DEMO_REVIEW_TEMPLATES)

        for course_index, course in enumerate(courses):
            for review_slot in range(2):
                template_index = (course_index * 2 + review_slot) % template_count
                review_text, rating, is_anonymous = DEMO_REVIEW_TEMPLATES[template_index]
                student_id = student_ids[
                    (course_index + review_slot) % len(student_ids)
                ]
                pending.append(
                    (
                        student_id,
                        CourseReviewCreate(
                            course_code=course.course_code,
                            rating=rating,
                            review_text=review_text,
                            is_anonymous=is_anonymous,
                        ),
                    )
                )
            updated_course_codes.add(course.course_code)

        reviews_inserted = repository.bulk_upsert_course_reviews(pending)
        repository.bulk_update_course_avg_ratings(updated_course_codes)

        return {
            "status": "success",
            "reviews_inserted": reviews_inserted,
            "courses_seeded": len(updated_course_codes),
            "invalid_course_codes": [],
            "message": (
                f"Inserted {reviews_inserted} demo review(s) "
                f"for {len(updated_course_codes)} course(s)."
            ),
        }

    def extract_course_skills(self, db_session: Session) -> int:
        repository = CourseRepository(db_session)
        assignments = [
            (
                course,
                resolve_skills_from_course_title(course.name or ""),
            )
            for course in repository.get_courses_for_pipeline()
        ]
        return repository.bulk_update_course_skills(assignments)

    def vectorize_courses(self, db_session: Session) -> int:
        repository = CourseRepository(db_session)
        updated = 0

        for course in repository.get_courses_with_skills_text():
            if not self._vector_is_missing(course.feature_vector):
                continue

            vector = self._embedding_service.get_embedding(course.skills)
            repository.update_course_feature_vector(course, vector)
            updated += 1

        return updated

    def compile_course_ratings(self, db_session: Session) -> int:
        repository = CourseRepository(db_session)
        averages = repository.get_average_ratings_by_course()
        updated = 0

        for course in repository.get_courses_for_pipeline():
            avg_rating = averages.get(course.course_code, 0.0)
            repository.update_course_avg_rating(course.course_code, avg_rating)
            updated += 1

        return updated

    @staticmethod
    def _vector_is_missing(vector: list[float] | None) -> bool:
        if vector is None:
            return True
        return not vector or bool(np.allclose(vector, 0.0))

"""Academic course data pipeline — seed, skill extraction, vectorization, ratings."""

from __future__ import annotations

from abc import ABC, abstractmethod

import bcrypt
import numpy as np
from sqlalchemy.orm import Session

from interfaces.embedding_service import EmbeddingService
from repositories.course_repository import CourseRepository

SEED_STUDENT_EMAILS: tuple[tuple[str, str], ...] = (
    ("pipeline.reviewer1@seed.local", "Seed Reviewer One"),
    ("pipeline.reviewer2@seed.local", "Seed Reviewer Two"),
    ("pipeline.reviewer3@seed.local", "Seed Reviewer Three"),
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

SKILL_RULES: tuple[tuple[str, str], ...] = (
    ("database", "SQL, Databases, PostgreSQL"),
    ("web", "JavaScript, React, Frontend, Backend, FastAPI"),
    ("algorithms", "Python, Algorithms, Data Structures"),
    ("cybersecurity", "Cybersecurity, Network Security"),
    ("cloud", "Cloud Computing, AWS, DevOps, Distributed Systems"),
)

DEFAULT_SKILLS = "Computer Science, Software Engineering"


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


class CoursePipelineServiceImpl(CoursePipelineService):
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self._embedding_service = embedding_service

    def seed_initial_courses_and_reviews(self, db_session: Session) -> dict:
        repository = CourseRepository(db_session)
        courses_inserted = 0
        reviews_inserted = 0
        students_inserted = 0

        seed_password = bcrypt.hashpw(
            b"pipeline-seed", bcrypt.gensalt()
        ).decode("utf-8")

        student_ids: list[int] = []
        for email, name in SEED_STUDENT_EMAILS:
            existing = repository.get_student_by_email(email)
            if existing:
                student_ids.append(existing.id)
                continue
            student = repository.create_seed_student(email, name, seed_password)
            student_ids.append(student.id)
            students_inserted += 1

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

    def extract_course_skills(self, db_session: Session) -> int:
        repository = CourseRepository(db_session)
        updated = 0

        for course in repository.get_courses_with_empty_skills():
            skills = self._skills_from_course_name(course.name or "")
            repository.update_course_skills(course, skills)
            updated += 1

        return updated

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
    def _skills_from_course_name(name: str) -> str:
        lowered = name.lower()
        for keyword, skills in SKILL_RULES:
            if keyword in lowered:
                return skills
        return DEFAULT_SKILLS

    @staticmethod
    def _vector_is_missing(vector: list[float] | None) -> bool:
        if vector is None:
            return True
        return not vector or bool(np.allclose(vector, 0.0))

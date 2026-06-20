import asyncio
import os
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional

_catalog_sync_lock = threading.Lock()
_catalog_synced = False

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload, noload, selectinload

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
        return (
            self._db.query(models.Course)
            .options(
                selectinload(models.Course.tracks),
                selectinload(models.Course.prerequisite_courses),
                noload(models.Course.linked_skills),
                noload(models.Course.occurrences),
            )
            .all()
        )

    def get_courses_by_categories(self, categories: List[str]) -> List[models.Course]:
        return (
            self._db.query(models.Course)
            .options(
                joinedload(models.Course.tracks),
                joinedload(models.Course.prerequisite_courses),
            )
            .filter(models.Course.category.in_(categories))
            .all()
        )

    def get_yearly_mandatory_map(self) -> dict[int, list[int]]:
        """Return real DB course_code values for mandatory courses, grouped by study year."""
        from services.mandatory_curriculum_catalog import (
            MANDATORY_CURRICULUM,
            YEAR_TO_CATEGORY,
        )

        yearly_map: dict[int, list[int]] = defaultdict(list)
        for spec in MANDATORY_CURRICULUM:
            if spec.year not in YEAR_TO_CATEGORY:
                continue
            course = self._resolve_curriculum_course(spec)
            if course and course.course_code not in yearly_map[spec.year]:
                yearly_map[spec.year].append(course.course_code)
        return {year: sorted(codes) for year, codes in yearly_map.items()}

    def get_course_reviews(self, course_code: int) -> List[models.CourseReview]:
        return (
            self._db.query(models.CourseReview)
            .filter(models.CourseReview.course_code == course_code)
            .all()
        )

    def delete_all_course_reviews(self) -> int:
        deleted = self._db.query(models.CourseReview).delete()
        self._db.query(models.Course).update(
            {models.Course.avg_rating: 0.0},
            synchronize_session=False,
        )
        self._db.commit()
        return deleted

    def get_course_by_code(self, course_code: int) -> Optional[models.Course]:
        return (
            self._db.query(models.Course)
            .options(
                joinedload(models.Course.tracks),
                joinedload(models.Course.prerequisite_courses),
            )
            .filter(models.Course.course_code == course_code)
            .first()
        )

    def get_course_by_short_code(self, short_code: int) -> Optional[models.Course]:
        """Match schedule/syllabus 5–6 digit codes against stored 7-digit course_code."""
        return (
            self._db.query(models.Course)
            .filter(
                (models.Course.course_code % 100000 == short_code)
                | (models.Course.course_code == short_code)
            )
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

    def _get_or_create_skill(
        self, name: str, cache: dict[str, models.Skill] | None = None
    ) -> models.Skill:
        if cache is None:
            cache = self._load_skill_cache()
        skill = cache.get(name)
        if skill is not None:
            return skill
        skill = models.Skill(name=name)
        self._db.add(skill)
        self._db.flush()
        cache[name] = skill
        return skill

    def _load_skill_cache(self) -> dict[str, models.Skill]:
        return {skill.name: skill for skill in self._db.query(models.Skill).all()}

    def sync_course_linked_skills(
        self,
        course: models.Course,
        skills_text: str,
        skill_cache: dict[str, models.Skill],
    ) -> bool:
        from services.course_skills_by_name import parse_skill_names

        changed = False
        if (course.skills or "") != skills_text:
            course.skills = skills_text
            changed = True

        skill_objects = [
            self._get_or_create_skill(name, skill_cache)
            for name in parse_skill_names(skills_text)
        ]
        existing_ids = {skill.id for skill in course.linked_skills}
        new_ids = {skill.id for skill in skill_objects}
        if existing_ids != new_ids:
            course.linked_skills = skill_objects
            changed = True
        return changed

    def ensure_course_skills_catalog(self) -> None:
        """Apply catalog skills to all courses (text + linked Skill rows)."""
        from services.course_skills_by_name import resolve_skills_for_course_name

        skill_cache = self._load_skill_cache()
        changed = False
        pending_commits = 0
        batch_size = int(os.getenv("CATALOG_SKILLS_COMMIT_BATCH", "20"))

        for course in self._db.query(models.Course).all():
            skills_text = resolve_skills_for_course_name(course.name or "")
            if not skills_text:
                continue
            if self.sync_course_linked_skills(course, skills_text, skill_cache):
                changed = True
                pending_commits += 1
                if pending_commits >= batch_size:
                    self._db.commit()
                    pending_commits = 0

        if changed and pending_commits > 0:
            self._db.commit()

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

    def commit(self) -> None:
        self._db.commit()

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
        self, course: models.Course, vector: list[float], *, commit: bool = True
    ) -> None:
        course.feature_vector = vector
        if commit:
            self._db.commit()

    def commit_session(self) -> None:
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

    def bulk_upsert_course_reviews(
        self, reviews: list[tuple[int, CourseReviewCreate]]
    ) -> int:
        if not reviews:
            return 0

        student_ids = {student_id for student_id, _ in reviews}
        course_codes = {review.course_code for _, review in reviews}
        existing_rows = (
            self._db.query(models.CourseReview)
            .filter(models.CourseReview.student_id.in_(student_ids))
            .filter(models.CourseReview.course_code.in_(course_codes))
            .all()
        )
        existing_map = {
            (row.student_id, row.course_code): row for row in existing_rows
        }

        inserted = 0
        for student_id, review in reviews:
            key = (student_id, review.course_code)
            existing = existing_map.get(key)
            if existing:
                existing.rating = review.rating
                existing.review_text = review.review_text
                existing.is_anonymous = review.is_anonymous
            else:
                db_review = models.CourseReview(
                    student_id=student_id,
                    course_code=review.course_code,
                    rating=review.rating,
                    review_text=review.review_text,
                    is_anonymous=review.is_anonymous,
                )
                self._db.add(db_review)
                existing_map[key] = db_review
            inserted += 1

        self._db.commit()
        return inserted

    def bulk_update_course_avg_ratings(self, course_codes: set[int]) -> None:
        if not course_codes:
            return
        averages = self.get_average_ratings_by_course()
        for course_code in course_codes:
            course = self.get_course_by_code(course_code)
            if course:
                course.avg_rating = averages.get(course_code, 0.0)
        self._db.commit()

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
        "ממשקי משתמש",
        "סייבר",
        "למידת מכונה",
    )

    _LEGACY_TRACK_NAME_MAP: dict[str, str] = {
        "Web Development": "ממשקי משתמש",
        "Cyber Security": "סייבר",
        "Data Science": "למידת מכונה",
    }

    def ensure_default_tracks(self) -> None:
        """Ensure canonical specialization tracks exist; migrate legacy English names."""
        changed = False
        for track in self.get_tracks():
            new_name = self._LEGACY_TRACK_NAME_MAP.get(track.name)
            if new_name and track.name != new_name:
                track.name = new_name
                changed = True
        if changed:
            self._db.commit()

        existing_names = {track.name for track in self.get_tracks()}
        added = False
        for name in self._DEFAULT_TRACK_NAMES:
            if name not in existing_names:
                self._db.add(models.Track(name=name))
                added = True
        if added:
            self._db.commit()

    def _build_curriculum_name_index(self) -> dict[str, models.Course]:
        return {course.name: course for course in self._db.query(models.Course).all()}

    def _resolve_curriculum_course(self, spec) -> Optional[models.Course]:
        for name in (spec.name, *spec.aliases):
            course = (
                self._db.query(models.Course)
                .filter(models.Course.name == name)
                .first()
            )
            if course:
                return course

        by_code = self.get_course_by_short_code(spec.code)
        if by_code and by_code.name == spec.name:
            return by_code

        return (
            self._db.query(models.Course)
            .filter(models.Course.name.contains(spec.name))
            .first()
        )

    def _resolve_prereq_course(
        self, prereq_name: str, by_name: dict[str, models.Course]
    ) -> Optional[models.Course]:
        from services.elective_curriculum_catalog import PREREQ_NAME_ALIASES

        for candidate in (prereq_name, PREREQ_NAME_ALIASES.get(prereq_name, prereq_name)):
            if candidate in by_name:
                return by_name[candidate]
            course = (
                self._db.query(models.Course)
                .filter(models.Course.name == candidate)
                .first()
            )
            if course:
                by_name[candidate] = course
                return course
        return None

    @staticmethod
    def _curriculum_category(spec) -> str:
        from services.mandatory_curriculum_catalog import YEAR_TO_CATEGORY, year_to_category

        if getattr(spec, "year", 0) in YEAR_TO_CATEGORY:
            return year_to_category(spec.year)
        return spec.category

    def _ensure_curriculum_specs(
        self,
        specs: tuple,
        by_name: dict[str, models.Course],
    ) -> None:
        from services.mandatory_curriculum_catalog import (
            format_prerequisites,
            spec_workload,
        )

        changed = False

        for spec in specs:
            category = self._curriculum_category(spec)
            course = self._resolve_curriculum_course(spec)
            if not course:
                workload = spec_workload(spec)
                course = models.Course(
                    course_code=spec.code,
                    name=spec.name,
                    category=category,
                    credits=spec.credits,
                    workload=workload,
                    semester_hours=workload,
                    mandatory_attendance=False,
                    prerequisites="",
                )
                self._db.add(course)
                changed = True

            by_name[spec.name] = course
            for alias in spec.aliases:
                by_name[alias] = course

        if changed:
            self._db.flush()

        for spec in specs:
            course = by_name.get(spec.name) or self._resolve_curriculum_course(spec)
            if not course:
                continue
            by_name[spec.name] = course

            workload = spec_workload(spec)
            prereq_text = format_prerequisites(spec)

            if course.name != spec.name:
                course.name = spec.name
                changed = True
            if course.category != category:
                course.category = category
                changed = True
            if course.credits != spec.credits:
                course.credits = spec.credits
                changed = True
            if course.workload != workload:
                course.workload = workload
                changed = True
            if course.semester_hours != workload:
                course.semester_hours = workload
                changed = True
            if (course.prerequisites or "") != prereq_text:
                course.prerequisites = prereq_text
                changed = True

            and_prereqs: list[models.Course] = []
            for prereq_name in spec.prereq_and:
                prereq = self._resolve_prereq_course(prereq_name, by_name)
                if prereq:
                    and_prereqs.append(prereq)

            # Query DB directly to avoid stale session cache on relationship
            from sqlalchemy import text as _text
            existing_codes = {
                row[0] for row in self._db.execute(
                    _text("SELECT prerequisite_code FROM course_prerequisites WHERE course_code = :c"),
                    {"c": course.course_code},
                ).fetchall()
            }
            new_codes = {p.course_code for p in and_prereqs}
            missing_codes = new_codes - existing_codes
            if missing_codes:
                for prereq_course in and_prereqs:
                    if prereq_course.course_code in missing_codes:
                        self._db.execute(
                            _text(
                                "INSERT INTO course_prerequisites (course_code, prerequisite_code)"
                                " VALUES (:c, :p) ON CONFLICT DO NOTHING"
                            ),
                            {"c": course.course_code, "p": prereq_course.course_code},
                        )
                changed = True

        if changed:
            self._db.commit()

    def ensure_mandatory_curriculum(self) -> None:
        """Upsert mandatory curriculum courses with credits, workload, and prerequisites."""
        from services.mandatory_curriculum_catalog import MANDATORY_CURRICULUM

        by_name = self._build_curriculum_name_index()
        self._ensure_curriculum_specs(MANDATORY_CURRICULUM, by_name)

    def ensure_elective_curriculum(self) -> None:
        """Upsert seminar and elective courses with credits, workload, and prerequisites."""
        from services.elective_curriculum_catalog import ELECTIVE_CURRICULUM

        by_name = self._build_curriculum_name_index()
        self._ensure_curriculum_specs(ELECTIVE_CURRICULUM, by_name)

    def ensure_track_catalog_courses(self) -> None:
        """Insert track elective courses that are missing from the courses table."""
        from services.track_courses_catalog import TRACK_COURSES

        changed = False
        seen_codes: set[int] = set()
        for entries in TRACK_COURSES.values():
            for entry in entries:
                if entry.code in seen_codes:
                    continue
                seen_codes.add(entry.code)

                course = self.get_course_by_short_code(entry.code)
                if not course:
                    course = (
                        self._db.query(models.Course)
                        .filter(models.Course.name == entry.name)
                        .first()
                    )
                if not course:
                    self._db.add(
                        models.Course(
                            course_code=entry.code,
                            name=entry.name,
                            category="elective",
                            workload=3,
                            mandatory_attendance=False,
                            prerequisites="",
                        )
                    )
                    changed = True
                elif course.name != entry.name:
                    course.name = entry.name
                    changed = True

        if changed:
            self._db.commit()

    def ensure_catalog_synced(self) -> None:
        """Run heavy catalog sync once per server process (not on every API call)."""
        global _catalog_synced
        if _catalog_synced:
            return

        from catalog_sync import get_sync_mode

        if get_sync_mode() == "skip":
            _catalog_synced = True
            return

        with _catalog_sync_lock:
            if _catalog_synced:
                return
            self.ensure_track_course_links()
            _catalog_synced = True

    def ensure_track_course_links(self) -> None:
        """Link catalog courses to each specialization track."""
        from services.track_courses_catalog import TRACK_COURSES

        self.ensure_default_tracks()
        self.ensure_mandatory_curriculum()
        self.ensure_elective_curriculum()
        self.ensure_course_skills_catalog()
        self.ensure_track_catalog_courses()
        changed = False
        for track_name, entries in TRACK_COURSES.items():
            track = (
                self._db.query(models.Track)
                .filter(models.Track.name == track_name)
                .first()
            )
            if not track:
                continue

            linked: list[models.Course] = []
            for entry in entries:
                course = self.get_course_by_short_code(entry.code)
                if course:
                    linked.append(course)

            existing_codes = {c.course_code for c in track.courses}
            new_codes = {c.course_code for c in linked}
            if existing_codes != new_codes:
                track.courses = linked
                changed = True

        if changed:
            self._db.commit()

        self.ensure_mandatory_attendance_rules()

    def ensure_mandatory_attendance_rules(self) -> None:
        """Apply attendance rules (seminars, intro SE, English, dev tools)."""
        from services.course_attendance_rules import course_requires_mandatory_attendance

        changed = False
        for course in self._db.query(models.Course).all():
            required = course_requires_mandatory_attendance(course.name)
            if course.mandatory_attendance != required:
                course.mandatory_attendance = required
                changed = True
        if changed:
            self._db.commit()

    def get_tracks(self) -> List[models.Track]:
        return self._db.query(models.Track).all()

    def get_job_roles(self) -> List[models.JobRole]:
        return self._db.query(models.JobRole).all()

    # --- Student profile & history ---

    def get_student_profile(self, student_id: int) -> models.StudentProfile:
        profile = (
            self._db.query(models.StudentProfile)
            .options(
                joinedload(models.StudentProfile.interested_tracks),
                joinedload(models.StudentProfile.interested_job_roles),
            )
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
            .options(joinedload(models.StudentCourseHistory.course))
            .filter(models.StudentCourseHistory.student_id == student_id)
            .order_by(models.StudentCourseHistory.course_code)
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

    def remove_student_course_history(
        self, student_id: int, course_code: int
    ) -> bool:
        existing = (
            self._db.query(models.StudentCourseHistory)
            .filter_by(student_id=student_id, course_code=course_code)
            .first()
        )
        if existing is None:
            return False
        self._db.delete(existing)
        self._db.commit()
        return True

    def get_planned_courses(self, student_id: int) -> List[models.PlannedCourse]:
        return (
            self._db.query(models.PlannedCourse)
            .options(
                joinedload(models.PlannedCourse.course).joinedload(
                    models.Course.tracks
                ),
                joinedload(models.PlannedCourse.course).joinedload(
                    models.Course.prerequisite_courses
                ),
                joinedload(models.PlannedCourse.course).joinedload(
                    models.Course.linked_skills
                ),
            )
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

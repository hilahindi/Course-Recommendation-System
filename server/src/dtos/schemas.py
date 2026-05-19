from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class TrackBase(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SkillBase(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class JobRoleBase(BaseModel):
    id: int
    title: str
    demand_level: str

    class Config:
        from_attributes = True


class CourseOccurrenceSchema(BaseModel):
    id: Optional[int] = None
    day_of_week: str
    start_time: str
    end_time: str
    room: Optional[str] = None
    lecturer: Optional[str] = None
    occurrence_type: Optional[str] = "הרצאה"

    class Config:
        from_attributes = True


class StudentAvailabilitySchema(BaseModel):
    id: Optional[int] = None
    day_of_week: str
    start_time: str
    end_time: str

    class Config:
        from_attributes = True


class CourseBase(BaseModel):
    course_code: int
    name: str
    category: Optional[str] = None
    workload: int
    credits: float = 3.0
    semester_hours: int = 3
    mandatory_attendance: bool
    prerequisites: str
    prerequisite_course_codes: List[int] = []
    has_exam: bool = True
    final_task_description: Optional[str] = None
    track_id: Optional[int] = None
    day_of_week: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    room: Optional[str] = None
    lecturer: Optional[str] = None
    occurrences: List[CourseOccurrenceSchema] = []
    skills: List[SkillBase] = Field(default_factory=list, validation_alias="linked_skills")

    @field_validator("skills", mode="before")
    @classmethod
    def coerce_skills(cls, value: object) -> object:
        if value is None or isinstance(value, str):
            return []
        return value

    class Config:
        from_attributes = True
        populate_by_name = True


class StudentCourseHistoryCreate(BaseModel):
    course_code: int
    grade: int


class StudentCourseHistoryBulkCreate(BaseModel):
    courses: List[StudentCourseHistoryCreate]


class StudentCourseHistoryResponse(BaseModel):
    id: int
    course_code: int
    grade: int
    course: CourseBase

    class Config:
        from_attributes = True


class PlannedCourseBase(BaseModel):
    course_code: int


class PlannedCourseResponse(PlannedCourseBase):
    id: int
    course: CourseBase

    class Config:
        from_attributes = True


class StudentProfileUpdate(BaseModel):
    target_workload: int
    needs_flexible_attendance: bool
    interested_track_ids: List[int]
    interested_job_role_ids: List[int]
    degree: Optional[str] = "Computer Science"
    year_of_study: Optional[int] = 1
    available_days: Optional[str] = ""
    availabilities: Optional[List[StudentAvailabilitySchema]] = None
    onboarding_completed: Optional[bool] = False


class StudentProfileResponse(BaseModel):
    id: int
    student_id: int
    target_workload: int
    needs_flexible_attendance: bool
    degree: str
    year_of_study: int
    available_days: str
    availabilities: List[StudentAvailabilitySchema] = []
    onboarding_completed: bool
    interested_tracks: List[TrackBase] = []
    interested_job_roles: List[JobRoleBase] = []

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    course: CourseBase
    score: int
    explanation: str


class AverageFeatureVectorResponse(BaseModel):
    vector: Optional[List[float]] = None
    dimension: int = 0
    job_count: int = 0
    source: str = "industry_jobs.feature_vector"


class CourseReviewCreate(BaseModel):
    course_code: int
    rating: int
    review_text: str
    is_anonymous: bool = False


class CourseReviewSubmit(BaseModel):
    course_code: int
    rating: int = Field(ge=1, le=5)
    review_text: str
    is_anonymous: bool = False


class CourseReviewResponse(BaseModel):
    id: int
    student_id: int
    course_code: int
    rating: int
    review_text: str
    is_anonymous: bool = False
    student_name: Optional[str] = None

    class Config:
        from_attributes = True


class CoursePipelineSeedResult(BaseModel):
    status: str
    courses_inserted: int
    reviews_inserted: int
    students_inserted: int
    message: str


class CoursePipelineStepResult(BaseModel):
    status: str
    updated_count: int
    message: str

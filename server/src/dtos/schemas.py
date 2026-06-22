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
    track_ids: List[int] = Field(default_factory=list)
    lecturer: Optional[str] = None
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
    onboarding_completed: Optional[bool] = False


class StudentProfileResponse(BaseModel):
    id: int
    student_id: int
    target_workload: int
    needs_flexible_attendance: bool
    degree: str
    year_of_study: int
    onboarding_completed: bool
    interested_tracks: List[TrackBase] = []
    interested_job_roles: List[JobRoleBase] = []

    class Config:
        from_attributes = True


class PrerequisiteSummary(BaseModel):
    code: int
    name: str


class RecommendationScoreBreakdown(BaseModel):
    track: int = 0
    industry: int = 0
    ratings: int = 0


class RecommendationResponse(BaseModel):
    course: CourseBase
    score: int
    explanation: str
    matching_skills: List[str] = []
    in_track_bundle: bool = False
    prerequisites_met: bool = True
    missing_prerequisites: List[PrerequisiteSummary] = []
    score_breakdown: RecommendationScoreBreakdown = RecommendationScoreBreakdown()


class AverageFeatureVectorResponse(BaseModel):
    vector: Optional[List[float]] = None
    dimension: int = 0
    job_count: int = 0
    source: str = "industry_jobs.feature_vector"


class CourseAdminUpsert(BaseModel):
    name: str
    category: Optional[str] = None
    workload: int = 3
    credits: float = 3.0
    semester_hours: int = 3
    has_exam: bool = True
    mandatory_attendance: bool = False
    prerequisites: str = ""
    skills: Optional[str] = None
    lecturer: Optional[str] = None


class CourseAdminCreate(CourseAdminUpsert):
    course_code: int


class UserRoleUpdate(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in ("student", "admin"):
            raise ValueError("role must be 'student' or 'admin'")
        return value


class AdminUserResponse(BaseModel):
    id: int
    name: Optional[str] = None
    email: str
    role: str

    class Config:
        from_attributes = True


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


class CourseReviewBulkItem(BaseModel):
    course_code: int
    rating: int = Field(ge=1, le=5)
    review_text: str
    is_anonymous: bool = False


class CourseReviewBulkCreate(BaseModel):
    reviews: List[CourseReviewBulkItem] = Field(min_length=1)


class CourseReviewSeedResult(BaseModel):
    status: str
    reviews_inserted: int
    courses_seeded: int = 0
    invalid_course_codes: List[int]
    message: str


class CourseReviewDeleteAllResult(BaseModel):
    status: str
    reviews_deleted: int
    message: str


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

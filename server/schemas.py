from pydantic import BaseModel
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
    workload: int
    credits: float = 3.0
    mandatory_attendance: bool
    prerequisites: str
    track_id: Optional[int] = None
    day_of_week: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    room: Optional[str] = None
    lecturer: Optional[str] = None
    skills: List[SkillBase] = []

    class Config:
        from_attributes = True

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

class StudentProfileUpdate(BaseModel):
    target_workload: int
    needs_flexible_attendance: bool
    interested_track_ids: List[int]
    interested_job_role_ids: List[int]
    degree: Optional[str] = "Computer Science"
    year_of_study: Optional[int] = 1
    available_days: Optional[str] = ""
    onboarding_completed: Optional[bool] = False

class StudentProfileResponse(BaseModel):
    id: int
    student_id: int
    target_workload: int
    needs_flexible_attendance: bool
    degree: str
    year_of_study: int
    available_days: str
    onboarding_completed: bool
    interested_tracks: List[TrackBase] = []
    interested_job_roles: List[JobRoleBase] = []

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    course: CourseBase
    score: int
    explanation: str

class CourseReviewCreate(BaseModel):
    course_code: int
    rating: int
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

class PlannedCourseBase(BaseModel):
    course_code: int

class PlannedCourseResponse(PlannedCourseBase):
    id: int
    course: CourseBase
    
    class Config:
        from_attributes = True

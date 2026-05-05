from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

# --- טבלאות קישור (Many-to-Many) ---

course_skill_link = Table(
    "course_skill_link",
    Base.metadata,
    Column("course_code", Integer, ForeignKey("courses.course_code"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True)
)

jobrole_skill_link = Table(
    "jobrole_skill_link",
    Base.metadata,
    Column("jobrole_id", Integer, ForeignKey("jobroles.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True)
)

profile_track_link = Table(
    "profile_track_link",
    Base.metadata,
    Column("profile_id", Integer, ForeignKey("student_profiles.id"), primary_key=True),
    Column("track_id", Integer, ForeignKey("tracks.id"), primary_key=True)
)

profile_jobrole_link = Table(
    "profile_jobrole_link",
    Base.metadata,
    Column("profile_id", Integer, ForeignKey("student_profiles.id"), primary_key=True),
    Column("jobrole_id", Integer, ForeignKey("jobroles.id"), primary_key=True)
)

# הטבלה החדשה לניהול דרישות קדם (קורס שמצביע לקורס אחר)
course_prerequisite_link = Table(
    "course_prerequisites",
    Base.metadata,
    Column("course_code", Integer, ForeignKey("courses.course_code"), primary_key=True),
    Column("prerequisite_code", Integer, ForeignKey("courses.course_code"), primary_key=True)
)

# --- מודלים ---

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) 

class Course(Base):
    __tablename__ = "courses"
    
    course_code = Column(Integer, primary_key=True, index=True) 
    name = Column(String, index=True)  
    category = Column(String, nullable=True, index=True) 
    workload = Column(Integer)
    credits = Column(Float, default=3.0) 
    
    # שדות אקדמיים חדשים
    semester_hours = Column(Integer, default=3)
    has_exam = Column(Boolean, default=True)
    final_task_description = Column(String, nullable=True)
    
    mandatory_attendance = Column(Boolean, default=False)
    prerequisites = Column(String, default="") # הטקסט הישן נשמר לגיבוי/תצוגה
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=True) 
    
    # שדות ישנים (נשמרים כדי לא לדרוס מידע קיים ב-DB)
    day_of_week = Column(String, nullable=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    room = Column(String, nullable=True)
    lecturer = Column(String, nullable=True)
    
    # קשרים (Relationships)
    occurrences = relationship("CourseOccurrence", back_populates="course", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary=course_skill_link, back_populates="courses")
    
    # הקשר החדש והחכם לדרישות קדם
    prerequisite_courses = relationship(
        "Course",
        secondary=course_prerequisite_link,
        primaryjoin="Course.course_code==course_prerequisites.c.course_code",
        secondaryjoin="Course.course_code==course_prerequisites.c.prerequisite_code",
        backref="is_prerequisite_for"
    )

class CourseOccurrence(Base):
    __tablename__ = "course_occurrences"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(Integer, ForeignKey("courses.course_code"))
    
    day_of_week = Column(String) 
    start_time = Column(String)  
    end_time = Column(String)    
    room = Column(String, nullable=True)
    lecturer = Column(String, nullable=True)
    occurrence_type = Column(String, nullable=True) 

    course = relationship("Course", back_populates="occurrences")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String)
    
    profile = relationship("StudentProfile", back_populates="student", uselist=False)

class StudentCourseHistory(Base):
    __tablename__ = "student_course_history"
    
    # מונע כפילויות: סטודנט לא יכול לקבל שני ציונים לאותו קורס
    __table_args__ = (UniqueConstraint('student_id', 'course_code', name='_student_course_uc'),)
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    course_code = Column(Integer, ForeignKey("courses.course_code"))
    grade = Column(Integer)
    
    student = relationship("Student", backref="course_history")
    course = relationship("Course")

class StudentAvailability(Base):
    """
    טבלה לניהול חלונות הזמן הפנויים של הסטודנט (החלפה של מחרוזת הטקסט הישנה)
    """
    __tablename__ = "student_availabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("student_profiles.id"))
    day_of_week = Column(String) 
    start_time = Column(String)  
    end_time = Column(String)    

    profile = relationship("StudentProfile", back_populates="availabilities")

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True)
    target_workload = Column(Integer, default=3)
    needs_flexible_attendance = Column(Boolean, default=False)
    
    degree = Column(String, default="Computer Science")
    year_of_study = Column(Integer, default=1)
    available_days = Column(String, default="") # נשאר לגיבוי
    onboarding_completed = Column(Boolean, default=False)
    
    # קשרים
    interested_tracks = relationship("Track", secondary=profile_track_link)
    interested_job_roles = relationship("JobRole", secondary=profile_jobrole_link)
    student = relationship("Student", back_populates="profile")
    
    # הקשר החדש לטבלת הזמינות
    availabilities = relationship("StudentAvailability", back_populates="profile", cascade="all, delete-orphan")

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    courses = relationship("Course", secondary=course_skill_link, back_populates="skills")
    jobroles = relationship("JobRole", secondary=jobrole_skill_link, back_populates="skills")

class JobRole(Base):
    __tablename__ = "jobroles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    demand_level = Column(String, default="Medium")
    
    skills = relationship("Skill", secondary=jobrole_skill_link, back_populates="jobroles")

class CourseReview(Base):
    __tablename__ = "course_reviews"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    course_code = Column(Integer, ForeignKey("courses.course_code"), index=True)
    rating = Column(Integer)
    review_text = Column(String)
    is_anonymous = Column(Boolean, default=False)

    student = relationship("Student")
    course = relationship("Course")

class PlannedCourse(Base):
    __tablename__ = "planned_courses"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    course_code = Column(Integer, ForeignKey("courses.course_code"), index=True)
    
    student = relationship("Student")
    course = relationship("Course")
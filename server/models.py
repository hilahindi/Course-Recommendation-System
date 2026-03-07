from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base

class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) 

class Course(Base):
    __tablename__ = "courses"
    
    course_code = Column(Integer, primary_key=True, index=True) 
    name = Column(String, index=True)                           
    workload = Column(Integer)                                 
    mandatory_attendance = Column(Boolean, default=False)      
    prerequisites = Column(String, default="")                 
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=True) 
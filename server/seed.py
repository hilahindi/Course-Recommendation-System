from database import SessionLocal, engine, Base
import models

# Create the database tables based on the models
models.Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()

    # Check if data already exists to avoid duplicates
    if db.query(models.Course).first():
        print("Data already exists in the database. No seeding required.")
    else:
        print("Creating tables and inserting Afeka sample data...")

        # Creating specialization tracks
        track_web = models.Track(name="Web Development")
        track_cyber = models.Track(name="Cyber Security")
        track_data = models.Track(name="Data Science")
        db.add_all([track_web, track_cyber, track_data])
        db.commit() 

        # Inserting courses
        courses = [
            # Core Courses
            models.Course(course_code=1001, name="Intro to Computer Science", workload=5, mandatory_attendance=True, prerequisites="", track_id=None),
            models.Course(course_code=1002, name="Data Structures", workload=5, mandatory_attendance=False, prerequisites="1001", track_id=None),
            models.Course(course_code=1003, name="Algorithms", workload=4, mandatory_attendance=False, prerequisites="1002", track_id=None),
            models.Course(course_code=1004, name="Operating Systems", workload=4, mandatory_attendance=True, prerequisites="1002", track_id=None),
            models.Course(course_code=1005, name="Computer Networks", workload=3, mandatory_attendance=False, prerequisites="1001", track_id=None),
            
            # Web Track Courses
            models.Course(course_code=2001, name="Web Application Development", workload=4, mandatory_attendance=False, prerequisites="1001", track_id=track_web.id),
            models.Course(course_code=2002, name="Advanced React", workload=3, mandatory_attendance=False, prerequisites="2001", track_id=track_web.id),
            
            # Cyber Track Courses
            models.Course(course_code=3001, name="Info Security Principles", workload=3, mandatory_attendance=True, prerequisites="1002", track_id=track_cyber.id),
            models.Course(course_code=3002, name="Network Security", workload=4, mandatory_attendance=True, prerequisites="1005,3001", track_id=track_cyber.id),
            
            # Data Track Courses
            models.Course(course_code=4001, name="Intro to Data Science", workload=3, mandatory_attendance=False, prerequisites="1002", track_id=track_data.id),
            models.Course(course_code=4002, name="Machine Learning", workload=5, mandatory_attendance=False, prerequisites="4001", track_id=track_data.id)
        ]
        
        db.add_all(courses)
        db.commit()
        print("Success: Database has been seeded with English data!")
    
    db.close()

if __name__ == "__main__":
    seed_data()
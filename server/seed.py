import os
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def seed_db():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create Tracks
    tracks_data = [
        {"id": 1, "name": "Cyber (סייבר)"},
        {"id": 2, "name": "User Interfaces (ממשקי משתמש - Web, Android, iOS)"},
        {"id": 3, "name": "Machine Learning (למידת מכונה)"}
    ]
    for td in tracks_data:
        t = db.query(models.Track).filter_by(id=td["id"]).first()
        if not t:
            t = models.Track(id=td["id"], name=td["name"])
            db.add(t)
    
    # Create Job Roles
    roles_data = [
        {"id": 1, "title": "Cloud Security Engineer", "demand_level": "High"},
        {"id": 2, "title": "Cybersecurity Analyst", "demand_level": "High"},
        {"id": 3, "title": "Prompt Engineer", "demand_level": "High"},
        {"id": 4, "title": "MLOps Engineer", "demand_level": "High"},
        {"id": 5, "title": "Data Scientist", "demand_level": "High"},
        {"id": 6, "title": "Full Stack Developer", "demand_level": "High"},
        {"id": 7, "title": "Frontend Engineer", "demand_level": "High"},
        {"id": 8, "title": "Mobile App Developer", "demand_level": "Medium"}
    ]
    for rd in roles_data:
        r = db.query(models.JobRole).filter_by(id=rd["id"]).first()
        if not r:
            r = models.JobRole(id=rd["id"], title=rd["title"], demand_level=rd["demand_level"])
            db.add(r)
            
    # Create Skills
    skills_data = [
        "Python", "Git", "Secure Coding", "Teamwork", "Industry Readiness", "React", "Machine Learning", "Data Analysis", "UI/UX", "iOS", "Android", "Web Development"
    ]
    db_skills = {}
    for s_name in skills_data:
        s = db.query(models.Skill).filter_by(name=s_name).first()
        if not s:
            s = models.Skill(name=s_name)
            db.add(s)
            db.commit()
            db.refresh(s)
        db_skills[s_name] = s

    # Assign skills to roles
    role_skills = {
        "Cloud Security Engineer": ["Secure Coding", "Python", "Git", "Industry Readiness"],
        "Cybersecurity Analyst": ["Secure Coding", "Data Analysis", "Industry Readiness"],
        "Prompt Engineer": ["Machine Learning", "Python", "Data Analysis"],
        "MLOps Engineer": ["Machine Learning", "Python", "Git", "Web Development"],
        "Data Scientist": ["Python", "Machine Learning", "Data Analysis", "Git"],
        "Full Stack Developer": ["React", "Web Development", "Git", "Teamwork", "Python"],
        "Frontend Engineer": ["React", "Web Development", "UI/UX", "Git"],
        "Mobile App Developer": ["iOS", "Android", "UI/UX", "Git", "Teamwork"]
    }
    db.commit()
    for role_title, s_names in role_skills.items():
        role = db.query(models.JobRole).filter_by(title=role_title).first()
        if role:
            role.skills = [db_skills[n] for n in s_names]

    # Create Courses
    # Cyber Cluster (Track 1)
    # UI Cluster (Track 2)
    # ML Cluster (Track 3)
    courses_data = [
        # Machine Learning
        {"code": 10127, "name": "Intro to AI / Databases", "workload": 4, "credits": 3.5, "track": 3, "skills": ["Python", "Machine Learning"]},
        {"code": 10245, "name": "Machine Learning", "workload": 5, "credits": 3, "track": 3, "skills": ["Python", "Machine Learning", "Data Analysis"]},
        {"code": 10224, "name": "Computer Vision", "workload": 4, "credits": 3, "track": 3, "skills": ["Python", "Machine Learning"]},
        {"code": 10359, "name": "Autonomous Vehicles & HMI in AI", "workload": 3, "credits": 2.5, "track": 3, "skills": ["Machine Learning", "Industry Readiness"]},
        {"code": 10240, "name": "Neural Networks & Deep Learning", "workload": 5, "credits": 3, "track": 3, "skills": ["Python", "Machine Learning"]},
        {"code": 10243, "name": "Neural Networks for Computer Vision", "workload": 4, "credits": 3, "track": 3, "skills": ["Python", "Machine Learning"]},
        {"code": 10351, "name": "Big Data Analysis", "workload": 3, "credits": 2.5, "track": 3, "skills": ["Data Analysis", "Python"]},
        {"code": 10206, "name": "Information Theory", "workload": 3, "credits": 3, "track": 3, "skills": ["Data Analysis"]},

        # Cyber
        {"code": 10147, "name": "UI Characterization", "workload": 4, "credits": 4, "track": 1, "skills": ["UI/UX", "Teamwork"]},
        {"code": 10313, "name": "Information Security", "workload": 3, "credits": 2.5, "track": 1, "skills": ["Secure Coding", "Industry Readiness"]},
        {"code": 10208, "name": "UI Development", "workload": 4, "credits": 4, "track": 1, "skills": ["Web Development", "React"]},
        {"code": 10233, "name": "Secure Development", "workload": 3, "credits": 2.5, "track": 1, "skills": ["Secure Coding", "Git"]},
        {"code": 10227, "name": "Cyber Security", "workload": 3, "credits": 2.5, "track": 1, "skills": ["Secure Coding"]},
        {"code": 10248, "name": "Modern Cryptography", "workload": 3, "credits": 2.5, "track": 1, "skills": ["Secure Coding", "Data Analysis"]},
        {"code": 10234, "name": "Mobile Security", "workload": 3, "credits": 2.5, "track": 1, "skills": ["Secure Coding", "iOS", "Android"]},
        {"code": 10228, "name": "Network Security", "workload": 3, "credits": 3, "track": 1, "skills": ["Secure Coding"]},

        # UI (some overlap with Cyber according to prompt)
        # 10147, 10313, 10208, 10234 are already above. We'll just add them to both tracks by setting track_id to UI, but wait - track_id is 1-to-many?
        # In models.py: Course.track_id = Column(Integer, ForeignKey("tracks.id")) => it's 1-to-many. A course can only belong to one track.
        # But the prompt says "Please ensure these specific courses are mapped to their respective clusters".
        # We'll just create the remaining UI ones and assign them to Track 2.
        {"code": 10220, "name": "Game Development", "workload": 3, "credits": 2.5, "track": 2, "skills": ["Teamwork", "UI/UX"]},
        {"code": 10225, "name": "Visual UI Design", "workload": 3, "credits": 2.5, "track": 2, "skills": ["UI/UX"]},
        {"code": 10219, "name": "iOS Development", "workload": 3, "credits": 2.5, "track": 2, "skills": ["iOS", "Git", "UI/UX"]},
        {"code": 10266, "name": "Web Platform Development", "workload": 4, "credits": 3, "track": 2, "skills": ["Web Development", "React", "Git"]}
    ]

    for cd in courses_data:
        c = db.query(models.Course).filter_by(course_code=cd["code"]).first()
        if not c:
            c = models.Course(
                course_code=cd["code"],
                name=cd["name"],
                workload=cd["workload"],
                credits=cd["credits"],
                track_id=cd["track"]
            )
            db.add(c)
        else:
            c.name = cd["name"]
            c.workload = cd["workload"]
            c.credits = cd["credits"]
            c.track_id = cd["track"]
        
        c.skills = [db_skills[n] for n in cd["skills"]]
        
    # Make sure overlap courses from Cyber are actually assigned to UI if they are more UI focused, or we just leave them in Cyber. 
    # Or we can just let them be in Cyber, as a course can only have one track_id.
    
    db.commit()
    db.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_db()
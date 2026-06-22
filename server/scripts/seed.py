from pathlib import Path
import sys

# Guarantee scripts/ is on sys.path (needed when cwd is server/ or project root)
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _bootstrap  # noqa: E402, F401
from _bootstrap import DATA_DIR

import os
import re
from database import SessionLocal, engine
import models

print("Deleting all existing tables to ensure clean schema...")
models.Base.metadata.drop_all(bind=engine)

print("Recreating tables with new schema...")
models.Base.metadata.create_all(bind=engine)

def extract_all_courses(base_directory):
    parsed_courses = {}
    
    # Make sure the base directory exists
    if not os.path.exists(base_directory):
        print(f"Directory {base_directory} not found.")
        return []

    patterns = {
        'lecturer': r"מרצה הקורס\s*:\s*(.*?)(?=\s*פרטים נוספים|\n|$)",
        'day': r"יום בשבוע:\s*יום\s+([א-ת]+)(?=\s*שעת|$)",
        'start_time': r"שעת התחלה\s*:\s*(\d{2}:\d{2})",
        'end_time': r"שעת סיום:\s*(\d{2}:\d{2})",
        'room': r"חדר לימוד:\s*(.*?)(?:\s\s+|\n|$)"
    }

    # os.walk scans the base directory and all of its subdirectories
    for root, dirs, files in os.walk(base_directory):
        
        # --- Extract the current folder name (e.g. "Mandatory A") ---
        folder_name = os.path.basename(root)
        # -------------------------------------------------------------

        for filename in files:
            if filename.endswith(".txt"):
                # Build the full path to the file
                file_path = os.path.join(root, filename)
                
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                    # 1. Extract the course name
                    name_match = re.search(r'קורס\s+(.+?)\s+שנה"ל', content)
                    course_name = name_match.group(1).strip() if name_match else None
                    
                    # 2. Extract the course code (first 7 digits)
                    code_match = re.search(r'קבוצה\s*:\s*(\d{7})', content)
                    course_code = int(code_match.group(1)) if code_match else None
                    
                    if course_name and course_code:
                        # Use a dict to avoid duplicates when a course has several groups
                        if course_code not in parsed_courses:
                            # Split into blocks by the course-type marker to extract extra fields (like extract.py)
                            blocks = re.split(r"קורס\s+מסוג", content)
                            
                            lecturer, day, start_time, end_time, room = "", "", "", "", ""
                            if len(blocks) > 1:
                                block = blocks[1]
                                def extract_val(pat):
                                    m = re.search(pat, block)
                                    return m.group(1).strip() if m else ""
                                
                                lecturer = extract_val(patterns['lecturer'])
                                day = extract_val(patterns['day'])
                                start_time = extract_val(patterns['start_time'])
                                end_time = extract_val(patterns['end_time'])
                                room = extract_val(patterns['room'])

                            parsed_courses[course_code] = {
                                "course_code": course_code,
                                "name": course_name,
                                "category": folder_name, # <-- add the category to the dict
                                "day_of_week": day,
                                "start_time": start_time,
                                "end_time": end_time,
                                "room": room,
                                "lecturer": lecturer
                            }
                            
    return list(parsed_courses.values())

def seed_data():
    db = SessionLocal()

    print("Clearing old data and scanning all text files for new course data...")
    
    # Delete old data from the tables to avoid duplicates
    from sqlalchemy import text
    db.execute(text("TRUNCATE TABLE courses, tracks CASCADE;"))
    db.commit()

    # Create the specialization tracks
    track_web = models.Track(name="ממשקי משתמש")
    track_cyber = models.Track(name="סייבר")
    track_data = models.Track(name="למידת מכונה")
    db.add_all([track_web, track_cyber, track_data])
    db.commit() 

    # Define the path to the base data directory (which contains all other folders)
    # Make sure this is the correct path relative to where you run the script
    base_data_path = str(DATA_DIR) 
    
    # Call the function that scans everything
    all_courses_data = extract_all_courses(base_data_path)
    
    courses_to_insert = []
    for course_data in all_courses_data:
        new_course = models.Course(
            course_code=course_data["course_code"],
            name=course_data["name"],
            category=course_data.get("category", ""), # <-- inject the category into the DB
            workload=3,                  # default value
            mandatory_attendance=False,  # default value
            prerequisites="", 
            track_id=None,
            lecturer=course_data.get("lecturer", "")
        )
        courses_to_insert.append(new_course)
        
    if courses_to_insert:
        db.add_all(courses_to_insert)
        db.commit()
        print(f"Success: Database has been seeded with {len(courses_to_insert)} unique courses from all folders!")
    else:
        print("No courses found. Please check your folder structure and paths.")

    from repositories.course_repository import CourseRepository

    CourseRepository(db).ensure_track_course_links()
    print("Linked specialization tracks to catalog courses.")

    db.close()

if __name__ == "__main__":
    seed_data()
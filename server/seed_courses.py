import re
import os
from database import SessionLocal, engine
import models
import random

root_folder = './data'

patterns = {
    'course_name': r"קורס (.*?) שנה\"ל",
    'group': r"קבוצה\s*:\s*([\d/ ]+)",
    'lecturer': r"מרצה הקורס\s*:\s*(.*?)(?=\s*פרטים נוספים|\n|$)",
    'day': r"יום בשבוע:\s*יום\s+([א-ת]+)(?=\s*שעת|$)",
    'start_time': r"שעת התחלה\s*:\s*(\d{2}:\d{2})",
    'end_time': r"שעת סיום:\s*(\d{2}:\d{2})",
    'room': r"חדר לימוד:\s*(.*?)(?:\s\s+|\n|$)"
}

def seed_courses():
    db = SessionLocal()
    
    for root, dirs, files in os.walk(root_folder):
        folder_category = os.path.basename(root)
        if folder_category == 'data': continue
        
        for filename in files:
            if filename.endswith(".txt"):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    course_match = re.search(patterns['course_name'], content)
                    course_name = course_match.group(1).strip() if course_match else None
                    if not course_name: continue
                    
                    blocks = re.split(r"קורס\s+מסוג", content)
                    if len(blocks) > 1:
                        block = blocks[1]
                        
                        lecturer_match = re.search(patterns['lecturer'], block)
                        lecturer = lecturer_match.group(1).strip() if lecturer_match else ""
                        
                        day_match = re.search(patterns['day'], block)
                        day_of_week = day_match.group(1).strip() if day_match else ""
                        
                        start_match = re.search(patterns['start_time'], block)
                        start_time = start_match.group(1).strip() if start_match else ""
                        
                        end_match = re.search(patterns['end_time'], block)
                        end_time = end_match.group(1).strip() if end_match else ""
                        
                        room_match = re.search(patterns['room'], block)
                        room = room_match.group(1).strip() if room_match else ""
                        
                        # Translate day to English for consistency if needed, or leave in Hebrew. We'll leave in Hebrew.
                        # Generate a course_code
                        course_code = int(abs(hash(course_name)) % 90000) + 10000
                        
                        # Check if exists
                        c = db.query(models.Course).filter_by(name=course_name).first()
                        if not c:
                            # Avoid collision
                            while db.query(models.Course).filter_by(course_code=course_code).first():
                                course_code += 1
                                
                            c = models.Course(
                                course_code=course_code,
                                name=course_name,
                                workload=random.randint(2, 5),
                                credits=random.choice([2.5, 3.0, 3.5, 4.0]),
                                track_id=None,
                                day_of_week=day_of_week,
                                start_time=start_time,
                                end_time=end_time,
                                room=room,
                                lecturer=lecturer
                            )
                            db.add(c)
                        else:
                            c.day_of_week = day_of_week
                            c.start_time = start_time
                            c.end_time = end_time
                            c.room = room
                            c.lecturer = lecturer
    
    db.commit()
    db.close()
    print("Courses seeded from data folder!")

if __name__ == "__main__":
    seed_courses()

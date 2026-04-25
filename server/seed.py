import os
import re
from database import SessionLocal, engine, Base
import models

print("Deleting all existing tables to ensure clean schema...")
models.Base.metadata.drop_all(bind=engine)

print("Recreating tables with new schema...")
models.Base.metadata.create_all(bind=engine)

def extract_all_courses(base_directory):
    parsed_courses = {}
    
    # נוודא שהתיקייה הראשית קיימת
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

    # os.walk סורק את התיקייה הראשית וכל תתי-התיקיות שקיימות בתוכה
    for root, dirs, files in os.walk(base_directory):
        
        # --- תוספת חדשה: חילוץ שם התיקייה הנוכחית (למשל "חובה א") ---
        folder_name = os.path.basename(root)
        # -------------------------------------------------------------

        for filename in files:
            if filename.endswith(".txt"):
                # מחבר את הנתיב המלא לקובץ
                file_path = os.path.join(root, filename)
                
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                    # 1. חילוץ שם הקורס
                    name_match = re.search(r'קורס\s+(.+?)\s+שנה"ל', content)
                    course_name = name_match.group(1).strip() if name_match else None
                    
                    # 2. חילוץ מספר הקורס (7 ספרות ראשונות)
                    code_match = re.search(r'קבוצה\s*:\s*(\d{7})', content)
                    course_code = int(code_match.group(1)) if code_match else None
                    
                    if course_name and course_code:
                        # שימוש במילון כדי למנוע כפילויות של קורס שיש לו כמה קבוצות במערכת
                        if course_code not in parsed_courses:
                            # חלוקה לבלוקים לפי "קורס מסוג" כדי לחלץ את הנתונים הנוספים (כמו ב-extract.py)
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
                                "category": folder_name, # <-- הוספנו את הקטגוריה למילון
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
    
    # מחיקת הנתונים הישנים מהטבלאות כדי למנוע כפילויות
    from sqlalchemy import text
    db.execute(text("TRUNCATE TABLE courses, tracks CASCADE;"))
    db.commit()

    # יצירת מסלולי ההתמחות
    track_web = models.Track(name="Web Development")
    track_cyber = models.Track(name="Cyber Security")
    track_data = models.Track(name="Data Science")
    db.add_all([track_web, track_cyber, track_data])
    db.commit() 

    # הגדרת הנתיב לתיקיית הנתונים הראשית (שמכילה את כל שאר התיקיות)
    # ודאי שזהו הנתיב הנכון מאיפה שאת מריצה את הסקריפט
    base_data_path = "./data" 
    
    # קריאה לפונקציה החדשה שסורקת הכל
    all_courses_data = extract_all_courses(base_data_path)
    
    courses_to_insert = []
    for course_data in all_courses_data:
        new_course = models.Course(
            course_code=course_data["course_code"],
            name=course_data["name"],
            category=course_data.get("category", ""), # <-- הזרקת הקטגוריה ל-DB
            workload=3,                  # ערך דיפולטיבי
            mandatory_attendance=False,  # ערך דיפולטיבי
            prerequisites="", 
            track_id=None,
            day_of_week=course_data.get("day_of_week", ""),
            start_time=course_data.get("start_time", ""),
            end_time=course_data.get("end_time", ""),
            room=course_data.get("room", ""),
            lecturer=course_data.get("lecturer", "")
        )
        courses_to_insert.append(new_course)
        
    if courses_to_insert:
        db.add_all(courses_to_insert)
        db.commit()
        print(f"Success: Database has been seeded with {len(courses_to_insert)} unique courses from all folders!")
    else:
        print("No courses found. Please check your folder structure and paths.")
    
    db.close()

if __name__ == "__main__":
    seed_data()
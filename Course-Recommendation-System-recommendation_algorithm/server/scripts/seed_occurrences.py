from pathlib import Path
import sys

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _bootstrap  # noqa: E402, F401
from _bootstrap import DATA_DIR

import os
import re
from sqlalchemy.orm import Session
from database import SessionLocal
import models

def parse_course_file(file_path):
    """
    קורא קובץ טקסט ומחלץ את המועדים והקבוצות שלו בעזרת ביטויים רגולריים (Regex)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # חילוץ קוד הקורס (מחפש רצף של 7 ספרות)
    course_code_match = re.search(r'(\d{7})', content)
    if not course_code_match:
        return None
    
    course_code = int(course_code_match.group(1))
    
    # חיפוש מדויק של ימי השבוע כדי למנוע הידבקות מילים
    # וחיפוש של השעות, המרצה והחדר עד סוף השורה או עד המילה "קורס" הבאה
    pattern = re.compile(
        r"יום\s+(?P<day>ראשון|שני|שלישי|רביעי|חמישי|שישי).*?"
        r"שעת התחלה\s*:\s*(?P<start>\d{2}:\d{2}).*?"
        r"שעת סיום:\s*(?P<end>\d{2}:\d{2}).*?"
        r"מרצה:\s*(?P<lecturer>.*?)חדר לימוד:\s*(?P<room>.*?)(?=\n|קורס מסוג|$)", 
        re.DOTALL
    )

    occurrences = []
    for match in pattern.finditer(content):
        occurrences.append({
            "course_code": course_code,
            "day_of_week": match.group('day').strip(),
            "start_time": match.group('start').strip(),
            "end_time": match.group('end').strip(),
            "lecturer": match.group('lecturer').strip(),
            "room": match.group('room').strip(),
            "occurrence_type": "קבוצת לימוד" 
        })
    
    return occurrences

def seed_data():
    db: Session = SessionLocal()
    base_data_dir = str(DATA_DIR) 
    
    if not os.path.exists(base_data_dir):
        print(f"שגיאה: התיקייה {base_data_dir} לא נמצאה.")
        return

    print("מתחיל בסריקת תיקיות הקורסים...")
    
    total_added = 0
    courses_updated = 0
    
    # os.walk עובר על כל תתי-התיקיות (elective, year-A, וכו')
    for root, dirs, files in os.walk(base_data_dir):
        for filename in files:
            if filename.endswith(".txt"):
                file_path = os.path.join(root, filename)
                
                # חילוץ שם הקטגוריה מתוך שם התיקייה
                category_name = os.path.basename(root) 
                
                course_data = parse_course_file(file_path)
                
                if course_data:
                    for occ_data in course_data:
                        # וידוא שהקורס כבר קיים במסד הנתונים
                        course = db.query(models.Course).filter_by(course_code=occ_data['course_code']).first()
                        
                        if course:
                            # עדכון הקטגוריה של הקורס לפי שם התיקייה (אם רלוונטי)
                            if not course.category or course.category == "":
                                course.category = category_name
                                courses_updated += 1

                            # הוספת המועד הספציפי לקורס
                            new_occ = models.CourseOccurrence(**occ_data)
                            db.add(new_occ)
                            total_added += 1
                        else:
                            print(f"התראה: הקורס {occ_data['course_code']} לא נמצא בטבלת courses. מדלג על המועד.")
    
    db.commit()
    db.close()
    
    print("--- סיכום ---")
    print(f"מועדים (Occurrences) חדשים שנוספו: {total_added}")
    print(f"קורסים שקטגוריית התיקייה שלהם עודכנה: {courses_updated}")

if __name__ == "__main__":
    seed_data()
import re
import os
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "database": "course_recommender",
    "user": "admin",
    "password": "password123",
    "port": "5432"
}

root_folder = './data' 

patterns = {
    'course_name': r"קורס (.*?) שנה\"ל",
    'group': r"קבוצה\s*:\s*([\d/ ]+)",
    # מרצה: מחפש עד המילים "פרטים נוספים" או סוף שורה, ומנקה רווחים
    'lecturer': r"מרצה הקורס\s*:\s*(.*?)(?=\s*פרטים נוספים|\n|$)",
    'semester': r"סמסטר:\s*([א-ב])",
    # יום: עוצר בדיוק לפני המילה "שעת"
    'day': r"יום בשבוע:\s*יום\s+([א-ת]+)(?=\s*שעת|$)",
    'start_time': r"שעת התחלה\s*:\s*(\d{2}:\d{2})",
    'end_time': r"שעת סיום:\s*(\d{2}:\d{2})",
    # חדר: מחלץ את כל מה שמופיע אחרי "חדר לימוד" עד סוף השורה
    'room': r"חדר לימוד:\s*(.*?)(?:\s\s+|\n|$)"
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("Connected to PostgreSQL successfully!")

    count = 0
    # os.walk עובר על כל תתי התיקיות
    for root, dirs, files in os.walk(root_folder):
        # שם התיקייה הנוכחית (למשל: seminar, elective)
        folder_category = os.path.basename(root)
        
        # דילוג על תיקיית השורש 'data' עצמה אם היא ריקה מקבצים
        if folder_category == 'data':
            continue

        for filename in files:
            if filename.endswith(".txt"):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    course_match = re.search(patterns['course_name'], content)
                    course_name = course_match.group(1).strip() if course_match else "Unknown"

                    # חלוקה לבלוקים לפי "קורס מסוג"
                    blocks = re.split(r"קורס\s+מסוג", content)
                    
                    for block in blocks[1:]: 
                        data = {key: (re.search(pattern, block).group(1).strip() if re.search(pattern, block) else None) 
                                for key, pattern in patterns.items() if key != 'course_name'}

                        # הוספת העמודה החדשה: course_type (שם התיקייה)
                        insert_query = """
                            INSERT INTO courses (course_name, group_id, lecturer, semester, day_of_week, start_t, end_t, room, course_type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cur.execute(insert_query, (
                            course_name, data['group'], data['lecturer'], 
                            data['semester'], data['day'], data['start_time'], 
                            data['end_time'], data['room'], folder_category
                        ))
                        count += 1

    conn.commit()
    print(f"Success! Processed all subfolders and inserted {count} rows.")

except Exception as e:
    print(f"Error: {e}")
finally:
    if conn:
        cur.close()
        conn.close()
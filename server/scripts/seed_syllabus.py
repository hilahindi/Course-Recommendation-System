from pathlib import Path
import sys

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _bootstrap  # noqa: E402, F401
from _bootstrap import DATA_DIR

import os
import re
import pdfplumber
from database import SessionLocal
import models

SYLLABUS_DIR = DATA_DIR / "syllabus"


def extract_text_from_pdf(pdf_path):
    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
    except Exception as e:
        print(f"Error reading {os.path.basename(pdf_path)}: {e}")
        return None
    return "\n".join(pages) if pages else None


def parse_syllabus(pdf_path):
    filename = os.path.basename(pdf_path)

    # course code from filename: [syllabus]-10015_10959.pdf
    code_match = re.search(r'\[syllabus\]-(\d+)_', filename)
    if not code_match:
        return None
    syllabus_code = int(code_match.group(1))

    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None

    result = {"syllabus_course_code": syllabus_code}

    # credits — total credit points
    m = re.search(r'סה"כ נ"ז\s*([\d.]+)', text)
    if m:
        result["credits"] = float(m.group(1))
        result["workload"] = int(float(m.group(1)))

    # semester_hours — course scope (total weekly contact hours)
    m = re.search(r'היקף הקורס\s*([\d.]+)', text)
    if m:
        result["semester_hours"] = int(float(m.group(1)))

    # mandatory_attendance — attendance requirement
    if "ללא חובת נוכחות" in text:
        result["mandatory_attendance"] = False
    elif "חובת נוכחות" in text:
        result["mandatory_attendance"] = True

    # prerequisites (everything up to the advisory notice)
    m = re.search(
        r"תנאי קדם\s+(.*?)(?=לתשומת ליבך|נוכחות\s|מטרות\s|תקציר\s)",
        text,
        re.DOTALL,
    )
    if m:
        prereq = m.group(1).strip()
        if prereq:
            result["prerequisites"] = prereq

    # final_task_description — course abstract / summary
    m = re.search(
        r"תקציר\s+(.*?)(?=תוצרי למידה|נושאי הקורס|דגשים ונלווים|רכז הקורס|$)",
        text,
        re.DOTALL,
    )
    if m:
        summary = m.group(1).strip()
        if summary:
            result["final_task_description"] = summary[:1000]

    # Fallback: use the goals section when no abstract is found
    if "final_task_description" not in result:
        m = re.search(
            r"מטרות\s+(.*?)(?=תקציר|תוצרי למידה|$)",
            text,
            re.DOTALL,
        )
        if m:
            goals = m.group(1).strip()
            if goals:
                result["final_task_description"] = goals[:1000]

    # has_exam — final exam with weight > 0
    m = re.search(r"מבחן סופי\s+(\d+)", text)
    if m:
        result["has_exam"] = int(m.group(1)) > 0

    return result


def seed_syllabus():
    db = SessionLocal()
    updated = 0
    not_found = 0
    errors = 0

    for root, _dirs, files in os.walk(SYLLABUS_DIR):
        for filename in sorted(files):
            if not filename.lower().endswith(".pdf"):
                continue

            pdf_path = os.path.join(root, filename)
            data = parse_syllabus(pdf_path)

            if not data:
                print(f"[SKIP] Could not parse: {filename}")
                errors += 1
                continue

            syllabus_code = data["syllabus_course_code"]

            # The schedule system stores the first 7 digits of the 9-digit group
            # code (e.g. 261001333 → 2610013). The actual 5-digit course code is
            # the last 5 digits of that 7-digit value (2610013 % 100000 = 10013).
            course = (
                db.query(models.Course)
                .filter(models.Course.course_code % 100000 == syllabus_code)
                .first()
            )

            # Fallback: exact match in case the code was stored differently
            if not course:
                course = (
                    db.query(models.Course)
                    .filter(models.Course.course_code == syllabus_code)
                    .first()
                )

            if not course:
                print(f"[NOT FOUND] syllabus code {syllabus_code} — {filename}")
                not_found += 1
                continue

            if "credits" in data:
                course.credits = data["credits"]
            if "workload" in data:
                course.workload = data["workload"]
            if "semester_hours" in data:
                course.semester_hours = data["semester_hours"]
            if "mandatory_attendance" in data:
                course.mandatory_attendance = data["mandatory_attendance"]
            if "prerequisites" in data:
                course.prerequisites = data["prerequisites"]
            if "final_task_description" in data:
                course.final_task_description = data["final_task_description"]
            if "has_exam" in data:
                course.has_exam = data["has_exam"]

            print(f"[OK] {syllabus_code} — {course.name}")
            updated += 1

    db.commit()
    db.close()

    print("\n--- Summary ---")
    print(f"Updated:   {updated}")
    print(f"Not found: {not_found}")
    print(f"Errors:    {errors}")


if __name__ == "__main__":
    seed_syllabus()

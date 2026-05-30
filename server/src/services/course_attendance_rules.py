"""Rules for courses that require mandatory attendance."""


def course_requires_mandatory_attendance(course_name: str) -> bool:
    name = (course_name or "").strip()
    if not name:
        return False

    lower = name.lower()

    if "סמינר" in name:
        return True
    if "מבוא להנדסת תוכנ" in name:
        return True
    if "כלי פיתוח" in name:
        return True
    if "סדנה" in name and "תכנות מונחה" in name:
        return True
    if "אתיקה" in name and "הנדסת תוכנ" in name:
        return True
    if "אנגלית" in name or "english" in lower:
        return True

    return False

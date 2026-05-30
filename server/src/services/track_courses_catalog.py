"""Canonical elective courses per specialization track."""

from typing import NamedTuple


class TrackCourseEntry(NamedTuple):
    code: int
    name: str


TRACK_COURSES: dict[str, tuple[TrackCourseEntry, ...]] = {
    "למידת מכונה": (
        TrackCourseEntry(19101, "מבוא לבינה מלאכותית"),
        TrackCourseEntry(10127, "בסיסי נתונים"),
        TrackCourseEntry(10245, "למידת מכונה"),
        TrackCourseEntry(10224, "מבוא לראייה ממוחשבת"),
        TrackCourseEntry(10359, "רכבים אוטונומיים והנדסת אנוש בעולמות ה-AI"),
        TrackCourseEntry(10240, "רשתות נוירונים ולמידה עמוקה"),
        TrackCourseEntry(10243, "רשתות נוירונים לראייה ממוחשבת"),
        TrackCourseEntry(10351, "ניתוח נתוני עתק"),
        TrackCourseEntry(10206, "תורת המידע"),
    ),
    "סייבר": (
        TrackCourseEntry(10147, "אפיון ממשקי משתמש"),
        TrackCourseEntry(10313, "אבטחת מידע"),
        TrackCourseEntry(10208, "פיתוח ממשקי משתמש"),
        TrackCourseEntry(10233, "פיתוח מאובטח"),
        TrackCourseEntry(10227, "אבטחת סייבר"),
        TrackCourseEntry(10248, "קריפטוגרפיה מודרנית"),
        TrackCourseEntry(10234, "אבטחת מובייל"),
        TrackCourseEntry(10228, "אבטחת רשתות תקשורת"),
    ),
    "ממשקי משתמש": (
        TrackCourseEntry(10147, "אפיון ממשקי משתמש"),
        TrackCourseEntry(10313, "אבטחת מידע"),
        TrackCourseEntry(10208, "פיתוח ממשקי משתמש"),
        TrackCourseEntry(10234, "אבטחת מובייל"),
        TrackCourseEntry(10220, "פיתוח משחקים"),
        TrackCourseEntry(10225, "עיצוב חזותי של ממשקי משתמש"),
        TrackCourseEntry(10219, "פיתוח בסביבת IOS"),
        TrackCourseEntry(10266, "פיתוח בפלטפורמת WEB"),
    ),
}

TRACK_COURSE_CODES: dict[str, tuple[int, ...]] = {
    track: tuple(entry.code for entry in entries)
    for track, entries in TRACK_COURSES.items()
}

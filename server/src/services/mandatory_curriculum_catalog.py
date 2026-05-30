"""Mandatory B.Sc. computer-science curriculum (credits, workload, prerequisites)."""

from __future__ import annotations

import math
from typing import NamedTuple


class CurriculumCourseSpec(NamedTuple):
    code: int
    name: str
    credits: float
    category: str = "mandatory"
    aliases: tuple[str, ...] = ()
    prereq_and: tuple[str, ...] = ()
    prereq_or_groups: tuple[tuple[str, ...], ...] = ()
    prerequisites_text: str = ""


MandatoryCourseSpec = CurriculumCourseSpec


def credits_to_workload(credits: float) -> int:
    """Each credit (including half) counts as one weekly study hour."""
    if credits <= 0:
        return 0
    return math.ceil(credits)


def format_prerequisites(spec: CurriculumCourseSpec) -> str:
    if spec.prerequisites_text:
        return spec.prerequisites_text
    if not spec.prereq_and and not spec.prereq_or_groups:
        return ""

    segments: list[str] = []
    for group in spec.prereq_or_groups:
        if len(group) == 1:
            segments.append(group[0])
        else:
            segments.append(" או ".join(group))
    segments.extend(spec.prereq_and)
    return ", ".join(segments)


MANDATORY_CURRICULUM: tuple[MandatoryCourseSpec, ...] = (
    MandatoryCourseSpec(90101, "מבוא למדעי המחשב", 5),
    MandatoryCourseSpec(90102, "מתמטיקה בדידה", 5),
    MandatoryCourseSpec(90103, "חשבון דיפרנציאלי ואינטגרלי 1", 5),
    MandatoryCourseSpec(90104, "אלגברה ליניארית 1", 5),
    MandatoryCourseSpec(
        90105,
        "תכנות מונחה עצמים",
        5,
        prereq_and=("מבוא למדעי המחשב",),
    ),
    MandatoryCourseSpec(
        90106,
        "מבני נתונים",
        5,
        prereq_or_groups=(("מבוא למדעי המחשב", "תכנות מונחה עצמים"),),
        prereq_and=("מתמטיקה בדידה",),
    ),
    MandatoryCourseSpec(
        90107,
        "חשבון דיפרנציאלי ואינטגרלי 2",
        5,
        prereq_and=("חשבון דיפרנציאלי ואינטגרלי 1",),
    ),
    MandatoryCourseSpec(
        90108,
        "לוגיקה מתמטית למדעי המחשב",
        4,
        prereq_and=("מתמטיקה בדידה",),
    ),
    MandatoryCourseSpec(
        90109,
        "תכנון וניתוח אלגוריתמים",
        5,
        prereq_and=("מבני נתונים", "מתמטיקה בדידה"),
    ),
    MandatoryCourseSpec(
        90110,
        "מבוא למערכות הפעלה",
        4,
        aliases=("מערכות הפעלה",),
        prereq_and=("מבני נתונים",),
    ),
    MandatoryCourseSpec(
        90111,
        "מבוא להסתברות",
        4,
        aliases=("הסתברות",),
        prereq_and=("חשבון דיפרנציאלי ואינטגרלי 2",),
    ),
    MandatoryCourseSpec(
        90112,
        "ארגון המחשב ושפת סף",
        4,
        prereq_and=("מבוא למדעי המחשב",),
    ),
    MandatoryCourseSpec(
        90113,
        "מודלים חישוביים",
        4,
        prereq_and=("מתמטיקה בדידה", "לוגיקה מתמטית למדעי המחשב"),
    ),
    MandatoryCourseSpec(
        90114,
        "מבוא להנדסת תוכנה",
        4,
        prereq_and=("תכנות מונחה עצמים",),
    ),
    MandatoryCourseSpec(
        90116,
        "תקשורת מחשבים לתוכנה",
        4,
        prereq_or_groups=(("מבוא למערכות הפעלה", "ארגון המחשב ושפת סף"),),
    ),
    MandatoryCourseSpec(
        90117,
        "פרויקט גמר למדעים 1",
        3,
        prereq_and=("מבוא להנדסת תוכנה", "בסיסי נתונים"),
    ),
    MandatoryCourseSpec(
        90118,
        "פרויקט גמר למדעים 2",
        5,
        prereq_and=("פרויקט גמר למדעים 1",),
    ),
)

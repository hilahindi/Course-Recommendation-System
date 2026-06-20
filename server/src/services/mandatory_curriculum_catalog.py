"""Mandatory B.Sc. computer-science curriculum (credits, workload, prerequisites)."""

from __future__ import annotations

import math
from collections import defaultdict
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
    year: int = 0  # 1–3 for mandatory year-A/B/C; 0 for electives
    semester: int = 0  # 1–8 official semester slot; 0 = derive from DAG
    workload: int = 0  # weekly hours; 0 = ceil(credits)


MandatoryCourseSpec = CurriculumCourseSpec


def credits_to_workload(credits: float) -> int:
    """Each credit (including half) counts as one weekly study hour."""
    if credits <= 0:
        return 0
    return math.ceil(credits)


def spec_workload(spec: CurriculumCourseSpec) -> int:
    return spec.workload if spec.workload > 0 else credits_to_workload(spec.credits)


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


YEAR_TO_CATEGORY: dict[int, str] = {1: "year-A", 2: "year-B", 3: "year-C"}


def year_to_category(year: int) -> str:
    return YEAR_TO_CATEGORY[year]


def build_yearly_mandatory_map() -> dict[int, list[int]]:
    """Course codes grouped by study year (1–3) for onboarding auto-fill."""
    yearly: dict[int, list[int]] = defaultdict(list)
    for spec in MANDATORY_CURRICULUM:
        if spec.year in YEAR_TO_CATEGORY:
            yearly[spec.year].append(spec.code)
    return {year: sorted(codes) for year, codes in yearly.items()}


MANDATORY_CURRICULUM: tuple[MandatoryCourseSpec, ...] = (
    # ── שנה א' — סמסטר א' ────────────────────────────────────────────────
    MandatoryCourseSpec(
        90901,
        "חשבון דיפרנציאלי ואינטגרלי 1",
        5,
        aliases=('חדו"א 1',),
        year=1,
        semester=1,
        workload=6,
    ),
    MandatoryCourseSpec(
        90905,
        "אלגברה ליניארית 1",
        5,
        aliases=("אלגברה ליניארית",),
        year=1,
        semester=1,
        workload=6,
    ),
    MandatoryCourseSpec(
        10016,
        "מבוא למדעי המחשב",
        4.5,
        year=1,
        semester=1,
        workload=6,
    ),
    MandatoryCourseSpec(
        90926,
        "מתמטיקה בדידה",
        5,
        year=1,
        semester=1,
        workload=6,
    ),
    # ── שנה א' — סמסטר ב' ────────────────────────────────────────────────
    MandatoryCourseSpec(
        90902,
        "חשבון דיפרנציאלי ואינטגרלי 2",
        5,
        aliases=('חדו"א 2',),
        prereq_and=("חשבון דיפרנציאלי ואינטגרלי 1",),
        year=1,
        semester=2,
        workload=6,
    ),
    MandatoryCourseSpec(
        90911,
        "מבוא להסתברות",
        3.5,
        aliases=("הסתברות",),
        prereq_and=("חשבון דיפרנציאלי ואינטגרלי 2",),
        year=1,
        semester=2,
        workload=4,
    ),
    MandatoryCourseSpec(
        10128,
        "תכנות מונחה עצמים",
        4.5,
        prereq_and=("מבוא למדעי המחשב",),
        year=1,
        semester=2,
        workload=6,
    ),
    MandatoryCourseSpec(
        10145,
        "ארגון המחשב ושפת סף",
        5,
        prereq_and=("מבוא למדעי המחשב",),
        year=1,
        semester=2,
        workload=6,
    ),
    # ── שנה ב' — סמסטר א' ────────────────────────────────────────────────
    MandatoryCourseSpec(
        90923,
        "לוגיקה מתמטית למדעי המחשב",
        3.5,
        prereq_and=("מתמטיקה בדידה",),
        year=2,
        semester=3,
        workload=5,
    ),
    MandatoryCourseSpec(
        10117,
        "מבני נתונים",
        5,
        prereq_and=("תכנות מונחה עצמים", "מתמטיקה בדידה"),
        year=2,
        semester=3,
        workload=6,
    ),
    MandatoryCourseSpec(
        10010,
        "מבוא לתכנות מערכות",
        3,
        prereq_and=("ארגון המחשב ושפת סף",),
        year=2,
        semester=3,
        workload=4,
    ),
    MandatoryCourseSpec(
        90954,
        "אלגברה ליניארית 2",
        5,
        aliases=("אלגברה ליניארית2",),
        prereq_and=("אלגברה ליניארית 1",),
        year=2,
        semester=3,
        workload=6,
    ),
    MandatoryCourseSpec(
        19101,
        "מבוא לבינה מלאכותית",
        2.5,
        prereq_and=("מבני נתונים", "מבוא להסתברות"),
        year=2,
        semester=3,
        workload=3,
    ),
    # ── שנה ב' — סמסטר ב' ────────────────────────────────────────────────
    MandatoryCourseSpec(
        10013,
        "תקשורת מחשבים",
        3.5,
        aliases=("תקשורת מחשבים לתוכנה",),
        prereq_or_groups=(("מערכות הפעלה", "ארגון המחשב ושפת סף"),),
        year=2,
        semester=4,
        workload=4,
    ),
    MandatoryCourseSpec(
        10139,
        "מודלים חישוביים",
        5,
        prereq_and=("מתמטיקה בדידה", "לוגיקה מתמטית למדעי המחשב"),
        year=2,
        semester=4,
        workload=6,
    ),
    MandatoryCourseSpec(
        10120,
        "תכנון וניתוח אלגוריתמים",
        5,
        prereq_and=("מבני נתונים", "מתמטיקה בדידה"),
        year=2,
        semester=4,
        workload=6,
    ),
    MandatoryCourseSpec(
        10303,
        "מערכות הפעלה",
        3.5,
        aliases=("מבוא למערכות הפעלה",),
        prereq_and=("מבני נתונים",),
        year=2,
        semester=4,
        workload=4,
    ),
    # ── שנה ג' — סמסטר א' ────────────────────────────────────────────────
    MandatoryCourseSpec(
        10324,
        "מחשוב מקבילי ומבוזר",
        4,
        prereq_and=("מבוא לתכנות מערכות", "מערכות הפעלה"),
        year=3,
        semester=5,
        workload=5,
    ),
    MandatoryCourseSpec(
        10334,
        "קומפילציה",
        3.5,
        prereq_and=("מבני נתונים", "מבוא לתכנות מערכות"),
        year=3,
        semester=5,
        workload=4,
    ),
    MandatoryCourseSpec(
        11402,
        "פרויקט במדעי המחשב - חלק 1",
        4,
        aliases=("פרויקט גמר למדעים 1",),
        prerequisites_text="מבוא להנדסת תוכנה, בסיסי נתונים (במקביל)",
        year=3,
        semester=5,
        workload=2,
    ),
    MandatoryCourseSpec(
        10014,
        "מבוא להנדסת תוכנה",
        4,
        prereq_and=("תכנות מונחה עצמים",),
        year=3,
        semester=5,
        workload=5,
    ),
    # ── שנה ג' — סמסטר ב' ────────────────────────────────────────────────
    MandatoryCourseSpec(
        10121,
        "אלגוריתם מתקדם",
        4,
        aliases=("אלגוריתמים מתקדמים וסיבוכיות",),
        prereq_and=("תכנון וניתוח אלגוריתמים",),
        year=3,
        semester=6,
        workload=5,
    ),
    MandatoryCourseSpec(
        11403,
        "פרויקט במדעי המחשב - חלק 2",
        0,
        aliases=("פרויקט גמר למדעים 2",),
        prereq_and=("פרויקט במדעי המחשב - חלק 1",),
        year=3,
        semester=6,
        workload=2,
    ),
)

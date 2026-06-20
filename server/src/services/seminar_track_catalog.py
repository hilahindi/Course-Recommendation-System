"""Track-specific seminar recommendations (primary + shared fallback)."""

from __future__ import annotations

from services.mandatory_curriculum_catalog import CurriculumCourseSpec

# Real Afeka syllabus codes
DEFAULT_FALLBACK_SEMINAR_CODE = 11015

TRACK_PRIMARY_SEMINAR: dict[str, int] = {
    "למידת מכונה": 10355,
    "סייבר": 10352,
    "ממשקי משתמש": 10221,
}

# Legacy catalog codes still present in some DB rows
LEGACY_SEMINAR_CODES: dict[int, int] = {
    92001: 11015,
    92002: 10221,
    92003: 10352,
    92004: 10355,
    92005: 10356,
}

SEMINAR_CANONICAL_BY_NAME: dict[str, int] = {
    "סמינר במדעי המחשב": 11015,
    "סמינר מתקדם בטכנולוגיות סלולריות": 10221,
    "סמינר בסייבר": 10352,
    "סמינר בלמידה חישובית": 10355,
    "סמינר בשפות תכנות": 10356,
}

_FALLBACK_TRACK_SCORE = 0.65


def track_names_from_profile(profile) -> list[str]:
    return [track.name for track in (profile.interested_tracks or []) if track.name]


def _short_code(code: int) -> int:
    return code % 100000 if code >= 100000 else code


def canonical_seminar_code(code: int, name: str | None = None) -> int:
    """Map DB / legacy codes to the canonical Afeka seminar code."""
    short = _short_code(code)
    if short in LEGACY_SEMINAR_CODES:
        return LEGACY_SEMINAR_CODES[short]
    if name:
        trimmed = name.strip()
        if trimmed in SEMINAR_CANONICAL_BY_NAME:
            return SEMINAR_CANONICAL_BY_NAME[trimmed]
    return short


def _code_variants(code: int) -> frozenset[int]:
    short = _short_code(code)
    variants = {code, short}
    canonical = LEGACY_SEMINAR_CODES.get(short, short)
    variants.add(canonical)
    for legacy, mapped in LEGACY_SEMINAR_CODES.items():
        if mapped == canonical:
            variants.add(legacy)
    if code >= 100000:
        variants.add(code % 100000)
    return frozenset(variants)


def codes_match(a: int, b: int) -> bool:
    return bool(_code_variants(a) & _code_variants(b))


def code_in_set(code: int, codes: set[int]) -> bool:
    return any(codes_match(code, candidate) for candidate in codes)


def target_seminar_for_tracks(track_names: list[str]) -> int:
    """Primary seminar goal for degree roadmap (always the track seminar, not fallback-first)."""
    for name in track_names:
        primary = TRACK_PRIMARY_SEMINAR.get(name)
        if primary is not None:
            return primary
    return DEFAULT_FALLBACK_SEMINAR_CODE


def seminar_prerequisite_codes(
    seminar_code: int,
    name_to_code: dict[str, int],
) -> tuple[int, ...]:
    spec = _seminar_spec_for_code(seminar_code)
    if spec is None:
        return ()
    codes: list[int] = []
    for name in spec.prereq_and:
        code = name_to_code.get(name)
        if code is not None:
            codes.append(code)
    return tuple(codes)


def track_elective_priority_codes(track_names: list[str]) -> tuple[int, ...]:
    from services.track_courses_catalog import TRACK_COURSES

    ordered: list[int] = []
    seen: set[int] = set()
    for track_name in track_names:
        for entry in TRACK_COURSES.get(track_name, ()):
            if entry.code not in seen:
                seen.add(entry.code)
                ordered.append(entry.code)
    return tuple(ordered)


def build_seminar_path_plan(
    track_names: list[str],
    name_to_code: dict[str, int],
    exclude: set[int],
) -> tuple[int, tuple[int, ...]]:
    """
    Returns ``(target_seminar, ordered_path_electives)``.
    Path electives: seminar prerequisites first, then remaining track-bundle courses.
    """
    target = target_seminar_for_tracks(track_names) if track_names else DEFAULT_FALLBACK_SEMINAR_CODE
    path: list[int] = []
    seen: set[int] = set()

    def add(code: int) -> None:
        if code_in_set(code, exclude) or code in seen:
            return
        seen.add(code)
        path.append(code)

    for prereq in seminar_prerequisite_codes(target, name_to_code):
        add(prereq)
    for code in track_elective_priority_codes(track_names):
        add(code)
    return target, tuple(path)


def seminar_prerequisite_names(seminar_code: int) -> tuple[str, ...]:
    spec = _seminar_spec_for_code(seminar_code)
    if spec is None:
        return ()
    return spec.prereq_and


def ordered_seminar_candidates(track_names: list[str]) -> tuple[int, ...]:
    """Primary seminar per selected track, then shared fallback."""
    ordered: list[int] = []
    seen: set[int] = set()

    def add(code: int) -> None:
        if code not in seen:
            seen.add(code)
            ordered.append(code)

    for name in track_names:
        primary = TRACK_PRIMARY_SEMINAR.get(name)
        if primary is not None:
            add(primary)

    add(DEFAULT_FALLBACK_SEMINAR_CODE)
    return tuple(ordered)


def allowed_seminar_codes_for_tracks(track_names: list[str]) -> set[int]:
    """All code variants (canonical + legacy) permitted for the student's track(s)."""
    if not track_names:
        return set()

    allowed: set[int] = set()
    for code in ordered_seminar_candidates(track_names):
        allowed.update(_code_variants(code))
    return allowed


def is_seminar_course(
    course_code: int,
    category: str | None = None,
    course_name: str | None = None,
) -> bool:
    """True for catalog seminars even when the DB category is legacy (e.g. elective1)."""
    if (category or "") == "seminar":
        return True
    if course_name and course_name.strip().startswith("סמינר"):
        return True
    return _seminar_spec_for_code(course_code, course_name) is not None


def is_track_seminar_allowed(
    course_code: int,
    track_names: list[str],
    course_name: str | None = None,
) -> bool:
    if not track_names:
        return True
    if not is_seminar_course(course_code, None, course_name):
        return True
    canonical = canonical_seminar_code(course_code, course_name)
    allowed = {canonical_seminar_code(c) for c in ordered_seminar_candidates(track_names)}
    return canonical in allowed


def seminar_spec_for_code(code: int, name: str | None = None) -> CurriculumCourseSpec | None:
    return _seminar_spec_for_code(code, name)


def _seminar_spec_for_code(code: int, name: str | None = None) -> CurriculumCourseSpec | None:
    from services.elective_curriculum_catalog import ELECTIVE_CURRICULUM

    canonical = canonical_seminar_code(code, name)
    for spec in ELECTIVE_CURRICULUM:
        if spec.category != "seminar":
            continue
        if codes_match(spec.code, canonical):
            return spec
    return None


def _seminar_prereqs_met(
    spec: CurriculumCourseSpec,
    passed_codes: set[int],
    name_to_code: dict[str, int],
) -> bool:
    for name in spec.prereq_and:
        prereq_code = name_to_code.get(name)
        if prereq_code is None or not code_in_set(prereq_code, passed_codes):
            return False
    return True


def pick_seminar_code(
    track_names: list[str],
    exclude: set[int],
    *,
    passed_codes: set[int] | None = None,
    name_to_code: dict[str, int] | None = None,
) -> int | None:
    """First track-ordered seminar not excluded; prefers seminars with met prerequisites."""
    ready: list[int] = []
    blocked: list[int] = []

    for code in ordered_seminar_candidates(track_names):
        if code_in_set(code, exclude):
            continue
        spec = _seminar_spec_for_code(code)
        if (
            passed_codes is not None
            and name_to_code is not None
            and spec is not None
            and not _seminar_prereqs_met(spec, passed_codes, name_to_code)
        ):
            blocked.append(code)
            continue
        ready.append(code)

    if ready:
        return ready[0]
    for code in blocked:
        if codes_match(code, DEFAULT_FALLBACK_SEMINAR_CODE):
            return code
    return blocked[0] if blocked else None


def seminar_track_tier(
    course_code: int,
    track_names: list[str],
    course_name: str | None = None,
) -> str | None:
    """Return ``primary``, ``fallback``, or ``None`` for a seminar course."""
    canonical = canonical_seminar_code(course_code, course_name)
    for name in track_names:
        primary = TRACK_PRIMARY_SEMINAR.get(name)
        if primary is not None and codes_match(canonical, primary):
            return "primary"
    if codes_match(canonical, DEFAULT_FALLBACK_SEMINAR_CODE):
        return "fallback"
    return None


def seminar_track_score(
    course_code: int,
    track_names: list[str],
    course_name: str | None = None,
) -> float:
    tier = seminar_track_tier(course_code, track_names, course_name)
    if tier == "primary":
        return 1.0
    if tier == "fallback":
        return _FALLBACK_TRACK_SCORE
    return 0.0

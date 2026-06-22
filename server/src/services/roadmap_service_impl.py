"""
Degree roadmap builder using a Directed Acyclic Graph (DAG) of course prerequisites.

Algorithm:
  1. Build a DAG where nodes are courses and edges are prerequisite dependencies.
  2. Run Kahn's topological sort + longest-path to assign each course a DAG level
     (the minimum number of prerequisite "layers" that must come before it).
  3. Map DAG levels → semesters, enforcing the catalog's year-floor constraint
     (a year-2 course cannot appear before semester 3, regardless of its DAG level).
  4. Fill elective slots from the same personalized recommendations list shown in the
     UI — prerequisites expanded and scheduled before the courses that need them.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

from fastapi import HTTPException

import models
from interfaces.recommendation_service import RecommendationService
from repositories.course_repository import CourseRepository
from services.mandatory_curriculum_catalog import (
    MANDATORY_CURRICULUM,
    CurriculumCourseSpec,
)
from services.elective_curriculum_catalog import ELECTIVE_CURRICULUM, LEGACY_ELECTIVE_CODES
from services.roadmap_cache import get_or_compute as get_or_compute_roadmap
from services.seminar_track_catalog import (
    LEGACY_SEMINAR_CODES,
    code_in_set,
    codes_match,
    is_seminar_course,
    pick_seminar_code,
    seminar_prerequisite_codes,
    seminar_prerequisite_names,
    seminar_spec_for_code,
    target_seminar_for_tracks,
    track_names_from_profile,
    DEFAULT_FALLBACK_SEMINAR_CODE,
)
from sqlalchemy.orm import Session

# ------------------------------------------------------------------ constants

_PASSING_GRADE = 60
_ELECTIVES_REQUIRED = 6
_SEMINAR_REQUIRED = 1
_DEGREE_SEMESTERS = 6  # 3-year BSc — semesters 7–8 are never shown
# Cap applies only to system-generated recommended courses in the roadmap.
# Students may plan or take more than this per semester on their own.
_ROADMAP_RECOMMENDED_MAX_PER_SEMESTER = 8
_MAX_COURSES_PER_SEMESTER = _ROADMAP_RECOMMENDED_MAX_PER_SEMESTER
_PREFERRED_MAX_LOAD = 7  # balance target before hitting hard cap
_ELECTIVE_SPREAD_MIN_SEM = 3
_ELECTIVE_SPREAD_MAX_SEM = 4  # prefer years 1–2 for electives; year 3 only when needed
_YEAR3_FIRST_SEM = 5
_RECOMMENDATION_PLAN_LIMIT = 10  # same cap as the recommendations API

_ALL_CATALOG: tuple[CurriculumCourseSpec, ...] = MANDATORY_CURRICULUM + ELECTIVE_CURRICULUM

_SEMESTER_LABELS: dict[int, str] = {
    1: "שנה א׳ - סמסטר א׳",
    2: "שנה א׳ - סמסטר ב׳",
    3: "שנה ב׳ - סמסטר א׳",
    4: "שנה ב׳ - סמסטר ב׳",
    5: "שנה ג׳ - סמסטר א׳",
    6: "שנה ג׳ - סמסטר ב׳",
    7: "שנה ד׳ - סמסטר א׳",
    8: "שנה ד׳ - סמסטר ב׳",
}


# ------------------------------------------------------------------ DAG

class DegreePlanDAG:
    """
    Directed Acyclic Graph of course prerequisites.

    Nodes  : course codes (int)
    Edges  : code → prerequisite_code  (i.e. edges point *backward* to deps)

    Internally we store both directions:
      _prereqs    : code  → {prerequisite codes}   (in-edges)
      _dependents : code  → {dependent codes}       (out-edges, for BFS)
    """

    def __init__(self) -> None:
        self._prereqs: dict[int, set[int]] = {}
        self._dependents: dict[int, set[int]] = {}
        self._specs: dict[int, CurriculumCourseSpec] = {}

    # ---------------------------------------------------------------- build

    def add_course(
        self, spec: CurriculumCourseSpec, name_to_code: dict[str, int]
    ) -> None:
        code = spec.code
        self._specs[code] = spec
        self._prereqs.setdefault(code, set())
        self._dependents.setdefault(code, set())

        resolved = self._resolve_prereqs(spec, name_to_code)
        for prereq_code in resolved:
            self._prereqs[code].add(prereq_code)
            self._dependents.setdefault(prereq_code, set()).add(code)

    @staticmethod
    def _resolve_prereqs(
        spec: CurriculumCourseSpec, name_to_code: dict[str, int]
    ) -> set[int]:
        """
        Translate prerequisite *names* from the catalog into course codes.

        AND prerequisites  → all codes are required.
        OR groups          → pick the first resolvable name in each group
                             (conservative: earliest standard path).
        """
        codes: set[int] = set()

        for name in spec.prereq_and:
            c = name_to_code.get(name)
            if c and c != spec.code:
                codes.add(c)

        for group in spec.prereq_or_groups:
            for name in group:
                c = name_to_code.get(name)
                if c and c != spec.code:
                    codes.add(c)
                    break  # Only the first valid option per OR group

        return codes

    # ---------------------------------------------------------------- analysis

    def topological_order(self) -> list[int]:
        """
        Return all nodes in a valid topological order using Kahn's BFS.
        A node appears only after all its prerequisites have appeared.
        Time complexity: O(V + E)
        """
        in_degree: dict[int, int] = {
            code: len(prereqs) for code, prereqs in self._prereqs.items()
        }
        queue: deque[int] = deque(
            code for code, deg in in_degree.items() if deg == 0
        )
        order: list[int] = []
        while queue:
            code = queue.popleft()
            order.append(code)
            for dependent in self._dependents.get(code, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        # Append any unreachable nodes at the end
        seen = set(order)
        for code in self._prereqs:
            if code not in seen:
                order.append(code)
        return order

    def detect_cycle(self) -> Optional[list[int]]:
        """Return a list of nodes in a cycle, or None if the graph is acyclic."""
        visited: set[int] = set()
        rec_stack: set[int] = set()
        cycle_node: list[int] = []

        def dfs(node: int) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for dep in self._dependents.get(node, set()):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    cycle_node.append(dep)
                    return True
            rec_stack.discard(node)
            return False

        for code in list(self._prereqs):
            if code not in visited and dfs(code):
                return cycle_node

        return None

    def prereqs_of(self, code: int) -> set[int]:
        return self._prereqs.get(code, set())

    def all_codes(self) -> set[int]:
        return set(self._prereqs)


# ------------------------------------------------------------------ service

class RoadmapServiceImpl:
    """
    Builds a semester-by-semester degree roadmap using the prerequisite DAG.

    Semester assignment for a course C:
        dag_level(C) = longest path from any source to C in the DAG
        semester(C)  = max(year_floor(C), dag_level(C) + 1)

    where year_floor enforces the catalog's intended year placement
    (year 1 → semester ≥ 1, year 2 → semester ≥ 3, year 3 → semester ≥ 5).
    """

    def __init__(
        self,
        repository: CourseRepository,
        recommendation_service: RecommendationService,
    ) -> None:
        self._repository = repository
        self._recommendation_service = recommendation_service
        self._name_to_code: dict[str, int] = _build_name_to_code()
        self._code_to_spec: dict[int, CurriculumCourseSpec] = {
            s.code: s for s in _ALL_CATALOG
        }
        self._dag: DegreePlanDAG = self._build_dag()

        cycle = self._dag.detect_cycle()
        if cycle:
            raise RuntimeError(f"Cycle detected in prerequisite graph: {cycle}")

    # ---------------------------------------------------------------- public

    async def build_roadmap(self, student_id: int, db_session: Session) -> dict:
        return await get_or_compute_roadmap(
            student_id,
            lambda: self._build_roadmap(student_id, db_session),
        )

    async def _build_roadmap(self, student_id: int, db_session: Session) -> dict:
        passed_codes = self._passed_codes(student_id, db_session)

        # Compute semester for electives / fallback placement via the DAG
        topo_order = self._dag.topological_order()
        sem_map = self._compute_semesters(topo_order)
        sem_map = self._balance_semesters(sem_map)

        semesters: dict[int, list[dict]] = {}

        # ── All mandatory courses (official semester slots from catalog) ───
        for spec in MANDATORY_CURRICULUM:
            sem = (
                spec.semester
                if spec.semester > 0
                else sem_map.get(spec.code, (spec.year - 1) * 2 + 1)
            )
            status = (
                "passed"
                if self._code_is_in_set(spec.code, passed_codes)
                else "upcoming"
            )
            semesters.setdefault(sem, []).append(
                _course_entry(spec, status, "mandatory")
            )

        # ── Passed electives (history) ─────────────────────────────────────
        passed_elective_codes = self._passed_elective_codes(passed_codes, db_session)
        for code in passed_elective_codes:
            spec = self._code_to_spec.get(self._catalog_code_for(code))
            if spec:
                sem = (
                    spec.semester
                    if spec.semester > 0
                    else sem_map.get(spec.code, 4)
                )
                entry = _course_entry(spec, "passed", spec.category or "elective")
            else:
                sem = 4
                name = _course_name_from_db(code, db_session)
                entry = {
                    "code": code,
                    "name": name,
                    "credits": 3.0,
                    "category": "elective",
                    "status": "passed",
                }
            semesters.setdefault(sem, []).append(entry)

        # ── Personalized recommended electives / seminars ──────────────────
        await self._fill_recommended_electives(
            semesters,
            passed_codes,
            passed_elective_codes,
            sem_map,
            student_id,
            db_session,
        )

        profile = self._repository.get_student_profile(student_id)
        track_names = track_names_from_profile(profile)
        target_seminar = (
            target_seminar_for_tracks(track_names)
            if track_names
            else DEFAULT_FALLBACK_SEMINAR_CODE
        )

        self._collapse_overflow_semesters(semesters, sem_map, passed_codes)
        self._enforce_semester_caps(semesters, sem_map, passed_codes)
        self._optimize_elective_timing(
            semesters, sem_map, passed_codes, target_seminar
        )
        self._enforce_seminar_prerequisite_order(
            semesters, sem_map, passed_codes, target_seminar
        )

        summary = self._build_summary(
            passed_codes, passed_elective_codes, db_session, track_names
        )

        return {
            "semesters": [
                {
                    "number": num,
                    "label": _SEMESTER_LABELS.get(num, f"סמסטר {num}"),
                    "courses": courses,
                }
                for num, courses in sorted(semesters.items())
                if num <= _DEGREE_SEMESTERS
            ],
            "summary": summary,
        }

    # ---------------------------------------------------------------- private

    def _build_dag(self) -> DegreePlanDAG:
        dag = DegreePlanDAG()
        for spec in _ALL_CATALOG:
            dag.add_course(spec, self._name_to_code)
        return dag

    def _balance_semesters(self, sem_map: dict[int, int]) -> dict[int, int]:
        """
        Post-process: for each academic year, move 'flexible' courses from the
        busier semester to the quieter one until the difference is at most 1.

        A course is moveable from sem_start → sem_end iff:
          1. No course currently in sem_start depends on it (prerequisite order preserved)
          2. None of its own prerequisites live in sem_end (it cannot come before them)
        """
        balanced = dict(sem_map)

        for year in range(1, 4):
            year_start = (year - 1) * 2 + 1
            year_end = year * 2

            start_courses = [c for c, s in balanced.items() if s == year_start]
            end_courses   = [c for c, s in balanced.items() if s == year_end]

            to_move = (len(start_courses) - len(end_courses)) // 2
            if to_move <= 0:
                continue

            moved = 0
            for code in start_courses:
                if moved >= to_move:
                    break
                dependents_in_start = [
                    d for d in self._dag._dependents.get(code, set())
                    if balanced.get(d) == year_start
                ]
                prereqs_in_end = [
                    p for p in self._dag._prereqs.get(code, set())
                    if balanced.get(p) == year_end
                ]
                if not dependents_in_start and not prereqs_in_end:
                    balanced[code] = year_end
                    moved += 1

        return balanced

    def _compute_semesters(self, topo_order: list[int]) -> dict[int, int]:
        """
        Compute the semester for every course by processing in topological order.

        For each course:
          natural_sem = max(semester of each prerequisite) + 1
          final_sem   = clamp(natural_sem, year_start, year_end)

        Clamping within [year_start, year_end] ensures that:
          - A year-2 course never appears before semester 3 (year_start = 3)
          - A year-1 course never spills into year 2 (year_end = 2)
          - Prerequisites within the same year correctly push courses to sem B
        """
        name_to_sem: dict[str, int] = {}
        code_to_sem: dict[int, int] = {}

        for code in topo_order:
            spec = self._code_to_spec.get(code)
            if not spec:
                continue

            if spec.semester > 0:
                final = spec.semester
                name_to_sem[spec.name] = final
                for alias in spec.aliases:
                    name_to_sem[alias] = final
                code_to_sem[code] = final
                continue

            if spec.year > 0:
                year_start = (spec.year - 1) * 2 + 1
                year_end = spec.year * 2
            else:
                year_start, year_end = 3, 8

            # Gather prerequisite semesters
            prereq_sems: list[int] = []
            for name in spec.prereq_and:
                s = name_to_sem.get(name, 0)
                if s:
                    prereq_sems.append(s)
            for group in spec.prereq_or_groups:
                for name in group:
                    s = name_to_sem.get(name, 0)
                    if s:
                        prereq_sems.append(s)
                        break

            natural = (max(prereq_sems) + 1) if prereq_sems else year_start
            final = max(year_start, min(natural, year_end))

            name_to_sem[spec.name] = final
            for alias in spec.aliases:
                name_to_sem[alias] = final
            code_to_sem[code] = final

        return code_to_sem

    async def _fill_recommended_electives(
        self,
        semesters: dict[int, list[dict]],
        passed_codes: set[int],
        passed_elective_codes: set[int],
        sem_map: dict[int, int],
        student_id: int,
        db_session: Session,
    ) -> None:
        """Plan the same recommended courses as the recommendations list, prerequisites first."""
        mandatory_codes = {s.code for s in MANDATORY_CURRICULUM}
        exclude = self._expand_code_variants(
            passed_codes | passed_elective_codes | mandatory_codes
        )

        passed_seminars = self._passed_seminar_count(passed_codes, db_session)
        passed_non_seminar = len(passed_elective_codes) - passed_seminars
        electives_needed = max(_ELECTIVES_REQUIRED - passed_non_seminar, 0)
        seminars_needed = max(_SEMINAR_REQUIRED - passed_seminars, 0)

        if electives_needed == 0 and seminars_needed == 0:
            return

        profile = self._repository.get_student_profile(student_id)
        track_names = track_names_from_profile(profile)

        recommendations = await self._fetch_recommendations(student_id, db_session)
        plan = self._build_plan_from_recommendations(
            recommendations,
            exclude,
            electives_needed,
            seminars_needed,
            passed_codes,
        )

        if not plan:
            self._fill_catalog_electives(
                semesters,
                exclude,
                sem_map,
                electives_needed,
                seminars_needed,
                track_names,
                passed_codes,
            )
            return

        placed_semesters: dict[int, int] = self._index_planned_semesters(semesters)
        non_seminar_total = sum(1 for _, cat in plan if cat != "seminar")
        non_seminar_idx = 0
        gateway_codes = set(
            seminar_prerequisite_codes(
                target_seminar_for_tracks(track_names) if track_names else DEFAULT_FALLBACK_SEMINAR_CODE,
                self._name_to_code,
            )
        )

        for code, category in plan:
            is_seminar = category == "seminar"
            floor = self._elective_floor_semester(
                code,
                sem_map,
                placed_semesters,
                passed_codes,
                semesters,
            )
            catalog = self._find_catalog_code(code)
            is_gateway = any(codes_match(catalog, g) for g in gateway_codes)
            if is_seminar:
                pref = self._seminar_semester_for_path(
                    catalog,
                    sem_map,
                    placed_semesters,
                    passed_codes,
                    semesters,
                )
            elif is_gateway:
                pref = max(floor, _YEAR3_FIRST_SEM)
            else:
                pref = max(
                    floor,
                    self._spread_preferred_semester(
                        non_seminar_idx,
                        max(non_seminar_total, 1),
                        floor,
                    ),
                )
                non_seminar_idx += 1

            sem = self._allocate_semester(
                semesters,
                pref,
                code,
                sem_map,
                is_seminar=is_seminar,
                floor_override=max(floor, pref) if is_seminar else floor,
            )
            canon = self._find_catalog_code(code)
            placed_semesters[canon] = sem
            placed_semesters[self._catalog_code_for(code)] = sem
            semesters.setdefault(sem, []).append(
                self._recommended_entry(code, category, db_session)
            )

        if electives_needed > sum(1 for _, c in plan if c != "seminar") or seminars_needed > sum(
            1 for _, c in plan if c == "seminar"
        ):
            placed_codes = {
                int(c.get("code", 0))
                for courses in semesters.values()
                for c in courses
                if c.get("status") == "recommended"
            }
            self._fill_catalog_electives(
                semesters,
                exclude | self._expand_code_variants(placed_codes),
                sem_map,
                electives_needed
                - sum(1 for _, c in plan if c != "seminar"),
                seminars_needed - sum(1 for _, c in plan if c == "seminar"),
                track_names,
                passed_codes,
                placed_semesters,
            )

    @staticmethod
    def _semester_load(semesters: dict[int, list[dict]], sem: int) -> int:
        return len(semesters.get(sem, []))

    @staticmethod
    def _spread_preferred_semester(
        index: int,
        total: int,
        min_sem: int,
        max_sem: int = _ELECTIVE_SPREAD_MAX_SEM,
    ) -> int:
        """Evenly spread elective placements across upper-year semesters."""
        floor = max(min_sem, _ELECTIVE_SPREAD_MIN_SEM)
        if total <= 1:
            return floor
        span = max_sem - floor
        if span <= 0:
            return floor
        return floor + (index * span) // (total - 1)

    def _allocate_semester(
        self,
        semesters: dict[int, list[dict]],
        preferred: int,
        code: int,
        sem_map: dict[int, int],
        *,
        is_seminar: bool = False,
        floor_override: int | None = None,
    ) -> int:
        """Pick a semester at or after *floor*, never before prerequisite timing."""
        floor = floor_override if floor_override is not None else max(
            preferred,
            self._semester_for_code(code, sem_map, preferred),
            _ELECTIVE_SPREAD_MIN_SEM if not is_seminar else _YEAR3_FIRST_SEM,
        )
        ceiling = _DEGREE_SEMESTERS
        floor = min(max(floor, 1), ceiling)

        def sort_key(sem: int) -> tuple[int, int, int, int]:
            load = self._semester_load(semesters, sem)
            soft_over = max(0, load - _PREFERRED_MAX_LOAD)
            year3_penalty = sem if (not is_seminar and sem >= _YEAR3_FIRST_SEM) else 0
            return (soft_over, load, year3_penalty, sem)

        with_capacity = [
            sem
            for sem in range(floor, ceiling + 1)
            if self._semester_load(semesters, sem) < _MAX_COURSES_PER_SEMESTER
        ]
        if with_capacity:
            return min(with_capacity, key=sort_key)

        # All slots in range are full — stay at/after floor (never spill to year 1).
        return min(range(floor, ceiling + 1), key=sort_key)

    def _collapse_overflow_semesters(
        self,
        semesters: dict[int, list[dict]],
        sem_map: dict[int, int],
        passed_codes: set[int],
    ) -> None:
        """Move courses from semesters 7+ into the 3-year window."""
        overflow: list[dict] = []
        for sem in list(semesters.keys()):
            if sem <= _DEGREE_SEMESTERS:
                continue
            overflow.extend(semesters.pop(sem, []))

        placed_after = self._index_planned_semesters(semesters)

        for entry in overflow:
            code = int(entry.get("code", 0))
            is_seminar = entry.get("category") == "seminar"
            if is_seminar:
                target = self._catalog_code_for(code)
                pref = self._seminar_semester_for_path(
                    target,
                    sem_map,
                    placed_after,
                    passed_codes,
                    semesters,
                )
            else:
                pref = self._semester_for_code(code, sem_map, 4)
            sem = self._allocate_semester(
                semesters,
                pref,
                code,
                sem_map,
                is_seminar=is_seminar,
                floor_override=pref if is_seminar else None,
            )
            semesters.setdefault(sem, []).append(entry)
            placed_after[self._catalog_code_for(code)] = sem

    def _enforce_semester_caps(
        self,
        semesters: dict[int, list[dict]],
        sem_map: dict[int, int],
        passed_codes: set[int],
    ) -> None:
        """Re-place recommended electives so every semester has at most 8 courses."""
        overloaded = any(
            self._semester_load(semesters, s) > _MAX_COURSES_PER_SEMESTER
            for s in range(1, _DEGREE_SEMESTERS + 1)
        )
        if not overloaded:
            return

        movable: list[dict] = []
        for sem in range(1, _DEGREE_SEMESTERS + 1):
            kept: list[dict] = []
            for course in semesters.get(sem, []):
                if (
                    course.get("status") == "recommended"
                    and course.get("category") not in ("seminar",)
                ):
                    movable.append(course)
                else:
                    kept.append(course)
            semesters[sem] = kept

        topo_index = {
            code: idx for idx, code in enumerate(self._dag.topological_order())
        }
        movable.sort(
            key=lambda entry: topo_index.get(
                self._find_catalog_code(int(entry.get("code", 0))), 9999
            )
        )
        placed_semesters = self._index_planned_semesters(semesters)
        non_seminar_total = len(movable)
        for idx, entry in enumerate(movable):
            code = int(entry.get("code", 0))
            floor = self._elective_floor_semester(
                code, sem_map, placed_semesters, passed_codes, semesters
            )
            spread = max(
                floor,
                self._spread_preferred_semester(
                    idx, max(non_seminar_total, 1), floor
                ),
            )
            sem = self._allocate_semester(semesters, spread, code, sem_map)
            if self._semester_load(semesters, sem) < _MAX_COURSES_PER_SEMESTER:
                semesters.setdefault(sem, []).append(entry)
                placed_semesters[self._catalog_code_for(code)] = sem

    def _resolve_elective_db_code(self, code: int) -> int:
        course = self._repository.get_course_by_short_code(code)
        if course:
            return course.course_code
        return code

    @staticmethod
    def _seminar_already_planned(seminar_code: int, exclude: set[int]) -> bool:
        return code_in_set(seminar_code, exclude)

    def _optimize_elective_timing(
        self,
        semesters: dict[int, list[dict]],
        sem_map: dict[int, int],
        passed_codes: set[int],
        target_seminar: int,
    ) -> None:
        """
        Pull seminar prerequisites into year 3 semester A and other ready electives
        into year 2; keep the seminar in year 3 semester B after its prerequisites.
        """
        gateway_codes = set(
            seminar_prerequisite_codes(target_seminar, self._name_to_code)
        )

        def pop_recommended(entry: dict) -> None:
            for sem, courses in semesters.items():
                if entry in courses:
                    semesters[sem] = [c for c in courses if c is not entry]
                    return

        def can_place(sem: int) -> bool:
            return self._semester_load(semesters, sem) < _MAX_COURSES_PER_SEMESTER

        def best_semester(
            floor: int,
            preferred: int,
            *,
            avoid_year3: bool = False,
        ) -> int:
            candidates = [
                sem
                for sem in range(max(floor, 1), _DEGREE_SEMESTERS + 1)
                if can_place(sem)
                and (not avoid_year3 or sem < _YEAR3_FIRST_SEM)
            ]
            if not candidates:
                return min(
                    range(max(floor, 1), _DEGREE_SEMESTERS + 1),
                    key=lambda s: self._semester_load(semesters, s),
                )
            return min(
                candidates,
                key=lambda s: (
                    abs(s - preferred),
                    max(0, self._semester_load(semesters, s) - _PREFERRED_MAX_LOAD),
                    self._semester_load(semesters, s),
                    s,
                ),
            )

        placed = self._index_planned_semesters(semesters)

        # Track elective prerequisites of gateway courses (e.g. UI specification) → year 2.
        gateway_prereqs: set[int] = set()
        for gateway in gateway_codes:
            for prereq in self._dag.prereqs_of(gateway):
                if self._is_elective_catalog_code(prereq):
                    gateway_prereqs.add(prereq)

        for sem in sorted(semesters.keys(), reverse=True):
            if sem <= _ELECTIVE_SPREAD_MAX_SEM:
                continue
            for entry in list(semesters.get(sem, [])):
                if entry.get("status") != "recommended":
                    continue
                if entry.get("category") == "seminar":
                    continue
                code = int(entry.get("code", 0))
                catalog = self._find_catalog_code(code)
                if not any(codes_match(catalog, p) for p in gateway_prereqs):
                    continue
                floor = self._elective_floor_semester(
                    code, sem_map, placed, passed_codes, semesters
                )
                if floor > _ELECTIVE_SPREAD_MAX_SEM:
                    continue
                target = best_semester(
                    max(floor, _ELECTIVE_SPREAD_MIN_SEM),
                    _ELECTIVE_SPREAD_MIN_SEM,
                    avoid_year3=True,
                )
                if target < sem:
                    pop_recommended(entry)
                    semesters.setdefault(target, []).append(entry)
                    placed = self._index_planned_semesters(semesters)

        placed = self._index_planned_semesters(semesters)

        # Seminar prerequisites (e.g. UI dev) → year 3 semester A when possible.
        for sem in sorted(semesters.keys()):
            for entry in list(semesters.get(sem, [])):
                if entry.get("status") != "recommended":
                    continue
                if entry.get("category") == "seminar":
                    continue
                code = int(entry.get("code", 0))
                catalog = self._find_catalog_code(code)
                if not any(codes_match(catalog, g) for g in gateway_codes):
                    continue
                floor = self._elective_floor_semester(
                    code, sem_map, placed, passed_codes, semesters
                )
                target = best_semester(
                    max(floor, _YEAR3_FIRST_SEM),
                    _YEAR3_FIRST_SEM,
                )
                if target != sem:
                    pop_recommended(entry)
                    semesters.setdefault(target, []).append(entry)
                    placed = self._index_planned_semesters(semesters)

        placed = self._index_planned_semesters(semesters)

        # Electives whose prerequisites are already satisfied → year 2 when possible.
        for sem in sorted(semesters.keys(), reverse=True):
            if sem <= _ELECTIVE_SPREAD_MAX_SEM:
                continue
            for entry in list(semesters.get(sem, [])):
                if entry.get("status") != "recommended":
                    continue
                if entry.get("category") == "seminar":
                    continue
                code = int(entry.get("code", 0))
                catalog = self._find_catalog_code(code)
                if any(codes_match(catalog, g) for g in gateway_codes):
                    continue
                floor = self._elective_floor_semester(
                    code, sem_map, placed, passed_codes, semesters
                )
                if floor > _ELECTIVE_SPREAD_MAX_SEM:
                    continue
                target = best_semester(
                    max(floor, _ELECTIVE_SPREAD_MIN_SEM),
                    _ELECTIVE_SPREAD_MAX_SEM,
                    avoid_year3=True,
                )
                if target < sem:
                    pop_recommended(entry)
                    semesters.setdefault(target, []).append(entry)
                    placed = self._index_planned_semesters(semesters)

    def _enforce_seminar_prerequisite_order(
        self,
        semesters: dict[int, list[dict]],
        sem_map: dict[int, int],
        passed_codes: set[int],
        target_seminar: int,
    ) -> None:
        """Move recommended seminars to the first semester after all planned prerequisites."""
        seminar_entries: list[dict] = []
        for sem in list(semesters.keys()):
            kept: list[dict] = []
            for course in semesters.get(sem, []):
                if (
                    course.get("status") == "recommended"
                    and course.get("category") == "seminar"
                ):
                    seminar_entries.append(course)
                else:
                    kept.append(course)
            semesters[sem] = kept

        for entry in seminar_entries:
            code = int(entry.get("code", 0))
            canon = self._catalog_code_for(code)
            lookup = (
                target_seminar
                if codes_match(canon, target_seminar)
                else canon
            )
            placed = self._index_planned_semesters(semesters)
            req_sem = self._seminar_semester_for_path(
                lookup, sem_map, placed, passed_codes, semesters
            )
            sem = self._allocate_semester(
                semesters,
                req_sem,
                code,
                sem_map,
                is_seminar=True,
                floor_override=req_sem,
            )
            semesters.setdefault(sem, []).append(entry)

    def _seminar_semester_for_path(
        self,
        seminar_code: int,
        sem_map: dict[int, int],
        placed_semesters: dict[int, int],
        passed_codes: set[int],
        semesters: dict[int, list[dict]],
        minimum: int = _YEAR3_FIRST_SEM,
    ) -> int:
        """Place the seminar in the first semester after its prerequisites."""
        prereq_sems: list[int] = []
        for prereq_code in seminar_prerequisite_codes(seminar_code, self._name_to_code):
            planned = self._planned_semester_for_code(
                prereq_code, semesters, placed_semesters, passed_codes, sem_map
            )
            if planned is not None:
                prereq_sems.append(planned)

        if prereq_sems:
            return min(
                _DEGREE_SEMESTERS,
                max(minimum, max(prereq_sems) + 1),
            )
        return min(
            _DEGREE_SEMESTERS,
            max(minimum, sem_map.get(self._catalog_code_for(seminar_code), minimum)),
        )

    def _planned_semester_for_code(
        self,
        code: int,
        semesters: dict[int, list[dict]],
        placed_semesters: dict[int, int],
        passed_codes: set[int],
        sem_map: dict[int, int],
    ) -> int | None:
        """Semester when a course is planned or None if already passed."""
        if self._code_is_in_set(code, passed_codes):
            return None
        catalog = self._find_catalog_code(code)
        if catalog in placed_semesters:
            return placed_semesters[catalog]
        for sem, courses in semesters.items():
            for course in courses:
                c_code = int(course.get("code", 0))
                if self._find_catalog_code(c_code) == catalog or codes_match(
                    c_code, code
                ):
                    return sem
        return sem_map.get(catalog)

    def _index_planned_semesters(
        self,
        semesters: dict[int, list[dict]],
    ) -> dict[int, int]:
        placed: dict[int, int] = {}
        for sem, courses in semesters.items():
            for course in courses:
                code = int(course.get("code", 0))
                canon = self._find_catalog_code(code)
                placed[canon] = sem
                placed[self._catalog_code_for(code)] = sem
                short = code % 100000 if code >= 100000 else code
                if short in LEGACY_ELECTIVE_CODES:
                    placed[short] = sem
                    placed[LEGACY_ELECTIVE_CODES[short]] = sem
        return placed

    async def _fetch_recommendations(
        self, student_id: int, db_session: Session
    ) -> list[dict]:
        """Same list the recommendations page uses."""
        try:
            return await self._recommendation_service.get_personalized_recommendations(
                db_session, student_id, limit=_RECOMMENDATION_PLAN_LIMIT
            )
        except Exception:
            return []

    def _find_catalog_code(self, code: int) -> int:
        catalog = self._catalog_code_for(code)
        if catalog in self._code_to_spec:
            return catalog
        for spec_code in self._code_to_spec:
            if codes_match(code, spec_code):
                return spec_code
        return catalog

    def _is_elective_catalog_code(self, catalog: int) -> bool:
        spec = self._code_to_spec.get(catalog)
        if spec is None:
            return True
        return spec.category in ("elective", "elective1", "seminar")

    def _build_plan_from_recommendations(
        self,
        recommendations: list[dict],
        exclude: set[int],
        electives_needed: int,
        seminars_needed: int,
        passed_codes: set[int],
    ) -> list[tuple[int, str]]:
        """
        Pick the same top recommended electives/seminar as the recommendations API,
        expand with their prerequisites, and return a prerequisite-safe order.
        """
        if electives_needed <= 0 and seminars_needed <= 0:
            return []

        rec_items: list[tuple[int, dict]] = []
        seen_catalog: set[int] = set()
        for item in recommendations:
            db_code = int(item["course"]["course_code"])
            if self._is_excluded(db_code, exclude):
                continue
            catalog = self._find_catalog_code(db_code)
            if catalog in seen_catalog:
                continue
            seen_catalog.add(catalog)
            rec_items.append((catalog, item))

        selected: list[int] = []
        added_electives = 0
        added_seminars = 0
        for catalog, item in rec_items:
            course = item["course"]
            db_code = int(course["course_code"])
            category = course.get("category") or "elective"
            name = course.get("name")
            is_seminar = is_seminar_course(db_code, category, name)
            if is_seminar:
                if added_seminars >= seminars_needed:
                    continue
                added_seminars += 1
                selected.append(catalog)
            else:
                if added_electives >= electives_needed:
                    continue
                added_electives += 1
                selected.append(catalog)

        if not selected:
            return []

        items_by_catalog = {catalog: item for catalog, item in rec_items}
        expanded: set[int] = set(selected)
        pending = list(selected)
        while pending:
            catalog = pending.pop()
            item = items_by_catalog.get(catalog)
            prereq_catalogs: set[int] = set()

            if item:
                for prereq in item.get("missing_prerequisites") or []:
                    pc = self._find_catalog_code(int(prereq["code"]))
                    if self._code_is_in_set(pc, passed_codes):
                        continue
                    if self._is_excluded(pc, exclude):
                        continue
                    prereq_catalogs.add(pc)

            for prereq in self._dag.prereqs_of(catalog):
                if not self._is_elective_catalog_code(prereq):
                    continue
                if self._code_is_in_set(prereq, passed_codes):
                    continue
                if self._is_excluded(prereq, exclude):
                    continue
                prereq_catalogs.add(prereq)

            for pc in prereq_catalogs:
                if pc not in expanded:
                    expanded.add(pc)
                    pending.append(pc)

        db_code_for: dict[int, int] = {}
        for catalog, item in rec_items:
            db_code_for[catalog] = int(item["course"]["course_code"])
        for catalog in expanded:
            if catalog not in db_code_for:
                db_code_for[catalog] = self._resolve_elective_db_code(catalog)

        ordered_catalogs: list[int] = [
            code for code in self._dag.topological_order() if code in expanded
        ]
        for catalog in expanded:
            if catalog not in ordered_catalogs:
                ordered_catalogs.append(catalog)

        plan: list[tuple[int, str]] = []
        for catalog in ordered_catalogs:
            db_code = db_code_for[catalog]
            item = items_by_catalog.get(catalog)
            if item:
                course = item["course"]
                category = course.get("category") or "elective"
                name = course.get("name")
            else:
                spec = self._code_to_spec.get(catalog)
                category = spec.category if spec else "elective"
                name = spec.name if spec else None
            display = (
                "seminar"
                if is_seminar_course(db_code, category, name)
                else "elective"
            )
            plan.append((db_code, display))
        return plan

    def _elective_floor_semester(
        self,
        code: int,
        sem_map: dict[int, int],
        placed_semesters: dict[int, int],
        passed_codes: set[int],
        semesters: dict[int, list[dict]],
    ) -> int:
        """Earliest semester allowed by DAG prerequisites already on the roadmap."""
        catalog = self._find_catalog_code(code)
        prereq_sems: list[int] = []
        for prereq in self._dag.prereqs_of(catalog):
            planned = self._planned_semester_for_code(
                prereq, semesters, placed_semesters, passed_codes, sem_map
            )
            if planned is not None:
                prereq_sems.append(planned)

        floor = max(
            _ELECTIVE_SPREAD_MIN_SEM,
            self._semester_for_code(code, sem_map, _ELECTIVE_SPREAD_MIN_SEM),
        )
        if prereq_sems:
            floor = max(floor, max(prereq_sems) + 1)
        return min(floor, _DEGREE_SEMESTERS)

    def _fill_catalog_electives(
        self,
        semesters: dict[int, list[dict]],
        exclude: set[int],
        sem_map: dict[int, int],
        electives_needed: int,
        seminars_needed: int,
        track_names: list[str] | None = None,
        passed_codes: set[int] | None = None,
        placed_semesters: dict[int, int] | None = None,
    ) -> None:
        """Fallback: first available catalog courses when personalization is unavailable."""
        if electives_needed <= 0 and seminars_needed <= 0:
            return

        passed_codes = passed_codes or set()
        placed_semesters = placed_semesters or self._index_planned_semesters(semesters)

        remaining = [
            s for s in ELECTIVE_CURRICULUM if not self._is_excluded(s.code, exclude)
        ]
        electives = [s for s in remaining if s.category != "seminar"]
        total = min(electives_needed, len(electives))

        for idx, spec in enumerate(electives[:electives_needed]):
            dag_min = max(
                _ELECTIVE_SPREAD_MIN_SEM,
                self._semester_for_code(spec.code, sem_map, _ELECTIVE_SPREAD_MIN_SEM),
            )
            spread_pref = self._spread_preferred_semester(idx, max(total, 1), dag_min)
            sem = self._allocate_semester(semesters, spread_pref, spec.code, sem_map)
            semesters.setdefault(sem, []).append(
                _course_entry(spec, "recommended", "elective")
            )

        if seminars_needed > 0:
            target = (
                target_seminar_for_tracks(track_names)
                if track_names
                else pick_seminar_code(
                    track_names or [],
                    exclude,
                    passed_codes=passed_codes,
                    name_to_code=self._name_to_code,
                )
            )
            if target is not None:
                db_code = self._seminar_code_for_db(target)
                catalog_code = self._catalog_code_for(db_code)
                spec = self._code_to_spec.get(catalog_code) or seminar_spec_for_code(target)
                if spec:
                    sem_pref = self._seminar_semester_for_path(
                        target,
                        sem_map,
                        placed_semesters,
                        passed_codes,
                        semesters,
                    )
                    sem = self._allocate_semester(
                        semesters,
                        sem_pref,
                        db_code,
                        sem_map,
                        is_seminar=True,
                        floor_override=sem_pref,
                    )
                    semesters.setdefault(sem, []).append(
                        _course_entry(spec, "recommended", "seminar")
                    )

    def _seminar_code_for_db(self, catalog_code: int) -> int:
        course = self._repository.get_course_by_short_code(catalog_code)
        if course:
            return course.course_code
        for legacy, canonical in LEGACY_SEMINAR_CODES.items():
            if codes_match(catalog_code, canonical):
                legacy_course = self._repository.get_course_by_short_code(legacy)
                if legacy_course:
                    return legacy_course.course_code
        return catalog_code

    @staticmethod
    def _code_is_in_set(code: int, codes: set[int]) -> bool:
        if code in codes:
            return True
        suffix = code % 100000
        return any(c % 100000 == suffix for c in codes)

    @staticmethod
    def _expand_code_variants(codes: set[int]) -> set[int]:
        expanded = set(codes)
        for code in codes:
            expanded.add(code % 100000)
        return expanded

    @staticmethod
    def _is_excluded(code: int, exclude: set[int]) -> bool:
        return code in exclude or (code % 100000) in exclude

    def _catalog_code_for(self, code: int) -> int:
        short = code % 100000 if code >= 100000 else code
        if short in LEGACY_ELECTIVE_CODES:
            return LEGACY_ELECTIVE_CODES[short]
        if code in self._code_to_spec:
            return code
        suffix = code % 100000
        for catalog_code in self._code_to_spec:
            if catalog_code % 100000 == suffix:
                return catalog_code
        return code

    def _semester_for_code(
        self, code: int, sem_map: dict[int, int], default: int
    ) -> int:
        catalog_code = self._catalog_code_for(code)
        spec = self._code_to_spec.get(catalog_code)
        if spec and spec.semester > 0:
            return spec.semester
        return sem_map.get(catalog_code, default)

    def _recommended_entry(
        self, code: int, category: str, db_session: Session
    ) -> dict:
        catalog_code = self._catalog_code_for(code)
        spec = self._code_to_spec.get(catalog_code)
        if spec:
            return _course_entry(spec, "recommended", category)

        course = (
            db_session.query(models.Course)
            .filter(models.Course.course_code == code)
            .first()
        )
        if not course:
            course = self._repository.get_course_by_short_code(code)
        if course:
            return {
                "code": course.course_code,
                "name": course.name,
                "credits": float(course.credits or 3),
                "category": category,
                "status": "recommended",
            }
        return {
            "code": code,
            "name": str(code),
            "credits": 3.0,
            "category": category,
            "status": "recommended",
        }

    def _passed_codes(self, student_id: int, db_session: Session) -> set[int]:
        history = self._repository.get_student_history(student_id)
        codes: set[int] = set()
        for h in history:
            if h.grade < _PASSING_GRADE:
                continue
            self._add_passed_code_variants(codes, h.course_code)
            course = h.course
            if course is None:
                course = (
                    db_session.query(models.Course)
                    .filter(models.Course.course_code == h.course_code)
                    .first()
                )
            if course and course.name:
                self._add_passed_codes_for_course_name(codes, course.name)
        return codes

    def _add_passed_code_variants(self, codes: set[int], code: int) -> None:
        codes.add(code)
        codes.add(code % 100000)
        catalog = self._catalog_code_for(code)
        codes.add(catalog)
        codes.add(catalog % 100000)

    def _add_passed_codes_for_course_name(self, codes: set[int], name: str) -> None:
        name = name.strip()
        if not name:
            return
        if name in self._name_to_code:
            self._add_passed_code_variants(codes, self._name_to_code[name])
            return
        for spec in MANDATORY_CURRICULUM:
            candidates = (spec.name, *spec.aliases)
            if any(
                name == n or name in n or n in name for n in candidates
            ):
                self._add_passed_code_variants(codes, spec.code)
                return
        for spec in ELECTIVE_CURRICULUM:
            candidates = (spec.name, *spec.aliases)
            if any(
                name == n or name in n or n in name for n in candidates
            ):
                self._add_passed_code_variants(codes, spec.code)
                return

    def _passed_elective_codes(
        self, passed_codes: set[int], db_session: Session
    ) -> set[int]:
        catalog_elective_codes = {s.code for s in ELECTIVE_CURRICULUM}
        db_elective_codes = {
            c.course_code
            for c in db_session.query(models.Course)
            .filter(models.Course.category.in_(["elective", "elective1", "seminar"]))
            .all()
        }
        mandatory_codes = {s.code for s in MANDATORY_CURRICULUM}
        return (passed_codes & (catalog_elective_codes | db_elective_codes)) - mandatory_codes

    def _passed_seminar_count(
        self, passed_codes: set[int], db_session: Session
    ) -> int:
        seminar_codes = {s.code for s in ELECTIVE_CURRICULUM if s.category == "seminar"}
        db_seminar_codes = {
            c.course_code
            for c in db_session.query(models.Course)
            .filter(models.Course.category == "seminar")
            .all()
        }
        return len(passed_codes & (seminar_codes | db_seminar_codes))

    def _build_summary(
        self,
        passed_codes: set[int],
        passed_elective_codes: set[int],
        db_session: Session,
        track_names: list[str] | None = None,
    ) -> dict:
        mandatory_codes = {s.code for s in MANDATORY_CURRICULUM}
        passed_mandatory = sum(
            1
            for spec in MANDATORY_CURRICULUM
            if self._code_is_in_set(spec.code, passed_codes)
        )
        passed_seminars = self._passed_seminar_count(passed_codes, db_session)
        passed_electives = len(passed_elective_codes) - passed_seminars

        total_needed = (
            len(MANDATORY_CURRICULUM) + _ELECTIVES_REQUIRED + _SEMINAR_REQUIRED
        )
        total_passed = passed_mandatory + passed_electives + passed_seminars
        completion_pct = round((total_passed / total_needed) * 100) if total_needed else 0

        summary: dict = {
            "passed_mandatory": passed_mandatory,
            "total_mandatory": len(MANDATORY_CURRICULUM),
            "passed_electives": passed_electives,
            "electives_needed": _ELECTIVES_REQUIRED,
            "passed_seminars": passed_seminars,
            "seminars_needed": _SEMINAR_REQUIRED,
            "completion_pct": completion_pct,
        }

        if track_names and passed_seminars < _SEMINAR_REQUIRED:
            target = target_seminar_for_tracks(track_names)
            spec = seminar_spec_for_code(target)
            missing_prereqs = [
                name
                for name in seminar_prerequisite_names(target)
                if not self._prereq_name_satisfied(name, passed_codes)
            ]
            summary["seminar_path"] = {
                "target_code": target,
                "target_name": spec.name if spec else str(target),
                "track": track_names[0],
                "missing_prerequisites": missing_prereqs,
            }

        return summary

    def _prereq_name_satisfied(self, name: str, passed_codes: set[int]) -> bool:
        code = self._name_to_code.get(name)
        if code is None:
            return False
        return self._code_is_in_set(code, passed_codes)


# ------------------------------------------------------------------ helpers

def _build_name_to_code() -> dict[str, int]:
    mapping: dict[str, int] = {}
    for spec in _ALL_CATALOG:
        mapping[spec.name] = spec.code
        for alias in spec.aliases:
            mapping[alias] = spec.code
    return mapping


def _course_entry(spec: CurriculumCourseSpec, status: str, category: str) -> dict:
    return {
        "code": spec.code,
        "name": spec.name,
        "credits": spec.credits,
        "category": category,
        "status": status,
    }


def _course_name_from_db(code: int, db_session: Session) -> str:
    course = db_session.query(models.Course).filter(
        models.Course.course_code == code
    ).first()
    return course.name if course else str(code)

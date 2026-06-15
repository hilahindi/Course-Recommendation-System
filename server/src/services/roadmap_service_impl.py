"""
Degree roadmap builder using a Directed Acyclic Graph (DAG) of course prerequisites.

Algorithm:
  1. Build a DAG where nodes are courses and edges are prerequisite dependencies.
  2. Run Kahn's topological sort + longest-path to assign each course a DAG level
     (the minimum number of prerequisite "layers" that must come before it).
  3. Map DAG levels → semesters, enforcing the catalog's year-floor constraint
     (a year-2 course cannot appear before semester 3, regardless of its DAG level).
  4. Fill elective slots with catalog suggestions, placed at their earliest valid semester.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

import models
from repositories.course_repository import CourseRepository
from services.mandatory_curriculum_catalog import (
    MANDATORY_CURRICULUM,
    CurriculumCourseSpec,
)
from services.elective_curriculum_catalog import ELECTIVE_CURRICULUM
from sqlalchemy.orm import Session

# ------------------------------------------------------------------ constants

_PASSING_GRADE = 60
_ELECTIVES_REQUIRED = 6
_SEMINAR_REQUIRED = 1

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

    def __init__(self, repository: CourseRepository) -> None:
        self._repository = repository
        self._name_to_code: dict[str, int] = _build_name_to_code()
        self._code_to_spec: dict[int, CurriculumCourseSpec] = {
            s.code: s for s in _ALL_CATALOG
        }
        self._dag: DegreePlanDAG = self._build_dag()

        cycle = self._dag.detect_cycle()
        if cycle:
            raise RuntimeError(f"Cycle detected in prerequisite graph: {cycle}")

    # ---------------------------------------------------------------- public

    def build_roadmap(self, student_id: int, db_session: Session) -> dict:
        passed_codes = self._passed_codes(student_id)

        # Compute semester for every course using topological order + clamping
        topo_order = self._dag.topological_order()
        sem_map = self._compute_semesters(topo_order)
        sem_map = self._balance_semesters(sem_map)

        semesters: dict[int, list[dict]] = {}

        # ── All mandatory courses ──────────────────────────────────────────
        for spec in MANDATORY_CURRICULUM:
            sem = sem_map.get(spec.code, (spec.year - 1) * 2 + 1)
            status = "passed" if spec.code in passed_codes else "upcoming"
            semesters.setdefault(sem, []).append(
                _course_entry(spec, status, "mandatory")
            )

        # ── Passed electives (history) ─────────────────────────────────────
        passed_elective_codes = self._passed_elective_codes(passed_codes, db_session)
        for code in passed_elective_codes:
            spec = self._code_to_spec.get(code)
            if spec:
                sem = sem_map.get(spec.code, 4)
                entry = _course_entry(spec, "passed", spec.category or "elective")
            else:
                sem = 4
                name = _course_name_from_db(code, db_session)
                entry = {"code": code, "name": name, "credits": 3.0,
                         "category": "elective", "status": "passed"}
            semesters.setdefault(sem, []).append(entry)

        # ── Top recommended electives (not yet passed) ─────────────────────
        self._fill_recommended_electives(
            semesters, passed_codes, passed_elective_codes, sem_map
        )

        summary = self._build_summary(passed_codes, passed_elective_codes, db_session)

        return {
            "semesters": [
                {
                    "number": num,
                    "label": _SEMESTER_LABELS.get(num, f"סמסטר {num}"),
                    "courses": courses,
                }
                for num, courses in sorted(semesters.items())
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

    def _fill_recommended_electives(
        self,
        semesters: dict[int, list[dict]],
        passed_codes: set[int],
        passed_elective_codes: set[int],
        sem_map: dict[int, int],
    ) -> None:
        """Add top recommended + required electives/seminars (not yet passed)."""
        mandatory_codes = {s.code for s in MANDATORY_CURRICULUM}
        exclude = passed_codes | passed_elective_codes | mandatory_codes
        remaining = [s for s in ELECTIVE_CURRICULUM if s.code not in exclude]

        seminars = [s for s in remaining if s.category == "seminar"]
        electives = [s for s in remaining if s.category != "seminar"]

        # Show enough electives to fill the required slots
        electives_done = len(passed_elective_codes)
        for spec in electives[:max(_ELECTIVES_REQUIRED - electives_done, 0)]:
            sem = sem_map.get(spec.code, 4)
            semesters.setdefault(sem, []).append(
                _course_entry(spec, "recommended", "elective")
            )

        seminars_done = sum(
            1 for c in passed_elective_codes
            if self._code_to_spec.get(c, None) and
               self._code_to_spec[c].category == "seminar"
        )
        for spec in seminars[:max(_SEMINAR_REQUIRED - seminars_done, 0)]:
            sem = sem_map.get(spec.code, 5)
            semesters.setdefault(sem, []).append(
                _course_entry(spec, "recommended", "seminar")
            )

    def _passed_codes(self, student_id: int) -> set[int]:
        history = self._repository.get_student_history(student_id)
        return {h.course_code for h in history if h.grade >= _PASSING_GRADE}

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
    ) -> dict:
        mandatory_codes = {s.code for s in MANDATORY_CURRICULUM}
        passed_mandatory = len(passed_codes & mandatory_codes)
        passed_electives = len(passed_elective_codes)
        passed_seminars = self._passed_seminar_count(passed_codes, db_session)

        total_needed = (
            len(MANDATORY_CURRICULUM) + _ELECTIVES_REQUIRED + _SEMINAR_REQUIRED
        )
        total_passed = passed_mandatory + passed_electives + passed_seminars
        completion_pct = round((total_passed / total_needed) * 100) if total_needed else 0

        return {
            "passed_mandatory": passed_mandatory,
            "total_mandatory": len(MANDATORY_CURRICULUM),
            "passed_electives": passed_electives,
            "electives_needed": _ELECTIVES_REQUIRED,
            "passed_seminars": passed_seminars,
            "seminars_needed": _SEMINAR_REQUIRED,
            "completion_pct": completion_pct,
        }


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

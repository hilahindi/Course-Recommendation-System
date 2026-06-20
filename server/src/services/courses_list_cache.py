"""In-process cache for the full course catalog list (changes rarely)."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import TypeVar

from dtos import CourseBase

T = TypeVar("T")

_cache: tuple[float, list[CourseBase]] | None = None
_CACHE_TTL_SECONDS = int(os.getenv("COURSES_LIST_CACHE_TTL_SECONDS", "600"))


def get_or_load_courses(load: Callable[[], list[CourseBase]]) -> list[CourseBase]:
    global _cache
    now = time.monotonic()
    if _cache is not None and now - _cache[0] < _CACHE_TTL_SECONDS:
        return _cache[1]

    courses = load()
    _cache = (now, courses)
    return courses


def invalidate_courses_list_cache() -> None:
    global _cache
    _cache = None

"""TTL + in-flight cache for expensive recommendation computations."""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Awaitable, Callable
from typing import Any

_lock = asyncio.Lock()
_inflight: dict[tuple[int, int], asyncio.Task[list[dict[str, Any]]]] = {}
_cache: dict[tuple[int, int], tuple[float, list[dict[str, Any]]]] = {}
_CACHE_TTL_SECONDS = int(os.getenv("RECOMMENDATION_CACHE_TTL_SECONDS", "300"))


def invalidate(student_id: int | None = None) -> None:
    if student_id is None:
        _cache.clear()
        return
    keys = [key for key in _cache if key[0] == student_id]
    for key in keys:
        _cache.pop(key, None)


async def get_or_compute(
    student_id: int,
    limit: int,
    compute: Callable[[], Awaitable[list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """
    Return cached recommendations when fresh; coalesce parallel requests.

    When the dashboard loads recommendations and roadmap at once, only one
    full computation runs; both callers receive the same result list.
    """
    key = (student_id, limit)
    now = time.monotonic()
    cached = _cache.get(key)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    async with _lock:
        cached = _cache.get(key)
        if cached and time.monotonic() - cached[0] < _CACHE_TTL_SECONDS:
            return cached[1]

        task = _inflight.get(key)
        if task is None:
            task = asyncio.create_task(compute())
            _inflight[key] = task

    try:
        result = await task
    finally:
        async with _lock:
            if _inflight.get(key) is task:
                _inflight.pop(key, None)

    _cache[key] = (time.monotonic(), result)
    return result

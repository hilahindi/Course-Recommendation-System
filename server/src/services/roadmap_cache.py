"""TTL + in-flight cache for expensive roadmap builds."""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Awaitable, Callable
from typing import Any

_lock = asyncio.Lock()
_inflight: dict[int, asyncio.Task[dict[str, Any]]] = {}
_cache: dict[int, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SECONDS = int(os.getenv("ROADMAP_CACHE_TTL_SECONDS", "300"))


def invalidate(student_id: int | None = None) -> None:
    if student_id is None:
        _cache.clear()
        return
    _cache.pop(student_id, None)


async def get_or_compute(
    student_id: int,
    compute: Callable[[], Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    now = time.monotonic()
    cached = _cache.get(student_id)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    key = student_id
    async with _lock:
        cached = _cache.get(student_id)
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

    _cache[student_id] = (time.monotonic(), result)
    return result

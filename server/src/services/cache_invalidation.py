"""Invalidate per-student response caches after profile/history changes."""

from __future__ import annotations

from services import recommendation_cache, roadmap_cache
from services.market_sync_cache import invalidate_market_sync


def invalidate_student_caches(student_id: int, *, refresh_market: bool = False) -> None:
    recommendation_cache.invalidate(student_id)
    roadmap_cache.invalidate(student_id)
    if refresh_market:
        invalidate_market_sync()
"""Per-role Adzuna sync throttle — always re-sync when the target role changes."""

from __future__ import annotations

import os
import time

_ROLE_LAST_SYNC: dict[str, float] = {}
_MARKET_SYNC_TTL_SECONDS = int(os.getenv("MARKET_SYNC_TTL_SECONDS", "3600"))


def _role_key(target_role: str) -> str:
    return target_role.strip().lower()


def needs_adzuna_sync(target_role: str) -> bool:
    """Return True when Adzuna should be queried for this role title."""
    if _MARKET_SYNC_TTL_SECONDS <= 0:
        return True

    key = _role_key(target_role)
    if not key:
        return True

    last_sync = _ROLE_LAST_SYNC.get(key)
    if last_sync is None:
        return True

    return (time.monotonic() - last_sync) >= _MARKET_SYNC_TTL_SECONDS


def record_adzuna_sync(target_role: str) -> None:
    key = _role_key(target_role)
    if key:
        _ROLE_LAST_SYNC[key] = time.monotonic()


def invalidate_market_sync(target_role: str | None = None) -> None:
    """Force the next recommendation request to pull fresh market data."""
    if target_role is None:
        _ROLE_LAST_SYNC.clear()
        return
    _ROLE_LAST_SYNC.pop(_role_key(target_role), None)

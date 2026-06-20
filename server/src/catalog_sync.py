"""Background / lazy course-catalog sync for local and remote PostgreSQL."""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Literal

logger = logging.getLogger(__name__)

SyncMode = Literal["blocking", "background", "skip"]
SyncStatus = Literal["pending", "running", "ready", "failed", "skipped"]

_state_lock = threading.Lock()
_state: dict[str, str | None] = {"status": "pending", "error": None}

_LOCAL_DB_MARKERS = ("localhost", "127.0.0.1", "@db:", "@db/")


def catalog_sync_status() -> dict[str, str | None]:
    with _state_lock:
        return dict(_state)


def _set_status(status: SyncStatus, error: str | None = None) -> None:
    with _state_lock:
        _state["status"] = status
        _state["error"] = error


def is_local_database(url: str | None = None) -> bool:
    db_url = url or os.getenv(
        "DATABASE_URL",
        "postgresql://admin:password123@127.0.0.1:5433/course_recommender",
    )
    return any(marker in db_url for marker in _LOCAL_DB_MARKERS)


def get_sync_mode() -> SyncMode:
    mode = os.getenv("CATALOG_SYNC_MODE", "").strip().lower()
    if mode in ("background", "blocking", "skip"):
        return mode  # type: ignore[return-value]
    return "blocking" if is_local_database() else "background"


def run_catalog_sync(*, max_attempts: int = 5) -> bool:
    """Sync catalog with retries and a fresh DB session per attempt."""
    from database import SessionLocal
    from repositories.course_repository import CourseRepository

    _set_status("running", None)

    for attempt in range(1, max_attempts + 1):
        db = SessionLocal()
        try:
            logger.info(
                "Catalog sync attempt %s/%s...",
                attempt,
                max_attempts,
            )
            CourseRepository(db).ensure_catalog_synced()
            _set_status("ready", None)
            logger.info("Catalog sync complete.")
            return True
        except Exception as exc:
            db.rollback()
            logger.warning(
                "Catalog sync attempt %s/%s failed: %s",
                attempt,
                max_attempts,
                exc,
            )
            _set_status("running", str(exc))
            if attempt < max_attempts:
                delay = min(30, 2**attempt)
                time.sleep(delay)
        finally:
            db.close()

    _set_status("failed", _state.get("error"))
    return False


def start_background_catalog_sync() -> threading.Thread:
    thread = threading.Thread(
        target=lambda: run_catalog_sync(max_attempts=5),
        name="catalog-sync",
        daemon=True,
    )
    thread.start()
    return thread


def bootstrap_catalog_sync() -> None:
    """Called once at app startup — never blocks remote DB connections indefinitely."""
    mode = get_sync_mode()
    if mode == "skip":
        _set_status("skipped", None)
        logger.info("Catalog sync skipped (CATALOG_SYNC_MODE=skip).")
        return

    if mode == "background":
        logger.info(
            "Starting catalog sync in background (remote DB or CATALOG_SYNC_MODE=background)."
        )
        start_background_catalog_sync()
        return

    logger.info("Running catalog sync before serving (local DB)...")
    if not run_catalog_sync(max_attempts=2):
        logger.error(
            "Catalog sync failed after retries; API will start and retry on first request."
        )

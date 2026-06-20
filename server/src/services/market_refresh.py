"""Shared Adzuna → skills → vectors pipeline used by recommendations and profile."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from interfaces.job_pipeline_service import JobPipelineService
from services.market_sync_cache import needs_adzuna_sync, record_adzuna_sync

logger = logging.getLogger(__name__)


async def refresh_market_data(
    db_session: Session,
    job_pipeline: JobPipelineService,
    target_role: str,
    *,
    force_adzuna: bool = False,
) -> int:
    """Pull listings for target_role and ensure skills/vectors are stored."""
    synced = 0
    role = target_role.strip()
    if not role:
        return 0

    try:
        if force_adzuna or needs_adzuna_sync(role):
            synced = await job_pipeline.sync_from_adzuna(db_session, role)
            record_adzuna_sync(role)
        job_pipeline.extract_skills_from_listings(db_session)
        job_pipeline.vectorize_listings(db_session)
    except Exception as exc:
        db_session.rollback()
        logger.warning("Market refresh failed for role %r: %s", role, exc)
    return synced


def target_role_from_job_role_ids(
    db_session: Session, job_role_ids: list[int]
) -> str | None:
    if not job_role_ids:
        return None
    import models

    role = (
        db_session.query(models.JobRole)
        .filter(models.JobRole.id == job_role_ids[0])
        .first()
    )
    if role and role.title:
        return role.title.strip()
    return None

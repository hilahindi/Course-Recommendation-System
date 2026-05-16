import json
import os

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict

import models
from database import get_db
from dtos import JobRoleBase, TrackBase
from repositories.course_repository import CourseRepository

import config  # noqa: F401 — loads server/.env

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])


def get_repository(db: Session = Depends(get_db)) -> CourseRepository:
    return CourseRepository(db)


@router.get("/", response_model=Dict[str, Any])
def read_metadata(repository: CourseRepository = Depends(get_repository)):
    try:
        tracks_db = repository.get_tracks()
        job_roles_db = repository.get_job_roles()
        return {
            "tracks": [TrackBase.model_validate(t) for t in tracks_db],
            "job_roles": [JobRoleBase.model_validate(j) for j in job_roles_db],
        }
    except Exception as e:
        print(f"Error in GET /metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metadata")


def sync_job_roles_from_ai(db: Session):
    """Sync market roles from AI. Callable from cron or HTTP."""
    try:
        prompt = """
        אתה מומחה קריירה וגיוס טכנולוגי בכיר בישראל. 
        מצא את 8 תפקידי הג'וניור (Entry Level) המבוקשים ביותר כרגע לבוגרי מדעי המחשב.
        החזר רשימת JSON נקייה ללא טקסט נוסף במבנה: 
        [{"title": "שם התפקיד בעברית", "demand_level": "High"}]
        """

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        ai_roles = json.loads(clean_json)

        try:
            db.query(models.JobRole).delete()
            db.commit()
        except Exception:
            db.rollback()
            print("Could not delete existing roles, updating instead.")

        added_count = 0
        for role_data in ai_roles:
            title = role_data.get("title")
            demand = role_data.get("demand_level", "High")
            existing_role = (
                db.query(models.JobRole).filter(models.JobRole.title == title).first()
            )
            if not existing_role:
                db.add(models.JobRole(title=title, demand_level=demand))
                added_count += 1

        db.commit()

        return {
            "message": "Market roles synchronized successfully",
            "added_new_roles": added_count,
            "roles_from_ai": ai_roles,
        }
    except Exception as e:
        db.rollback()
        print(f"AI Sync Error: {e}")
        raise HTTPException(status_code=500, detail=f"Claude AI Sync failed: {str(e)}")


@router.post("/sync-market-roles")
def sync_market_roles_endpoint(db: Session = Depends(get_db)):
    return sync_job_roles_from_ai(db)

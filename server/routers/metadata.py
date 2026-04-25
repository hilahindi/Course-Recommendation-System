import json
import os
import anthropic
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from dotenv import load_dotenv

import crud, schemas, models
from database import get_db

# טעינת משתני סביבה מקובץ .env
load_dotenv()

# אתחול הקליינט של קלוד באמצעות משתנה סביבה בלבד
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

router = APIRouter(
    prefix="/api/metadata",
    tags=["metadata"]
)

@router.get("/", response_model=Dict[str, Any])
def read_metadata(db: Session = Depends(get_db)):
    try:
        # שליפת הנתונים הגולמיים מהמסד
        tracks_db = crud.get_tracks(db)
        job_roles_db = crud.get_job_roles(db)
        
        # המרה לסכימות Pydantic
        return {
            "tracks": [schemas.TrackBase.model_validate(t) for t in tracks_db],
            "job_roles": [schemas.JobRoleBase.model_validate(j) for j in job_roles_db]
        }
    except Exception as e:
        print(f"Error in GET /metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metadata")

@router.post("/sync-market-roles")
def sync_job_roles_from_ai(db: Session = Depends(get_db)):
    """
    מסנכרן תפקידים מול ה-AI. 
    מוחק תפקידים ישנים שאין להם סטודנטים רשומים כדי למנוע כפילויות.
    """
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
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        clean_json = response_text.replace('```json', '').replace('```', '').strip()
        ai_roles = json.loads(clean_json)

        # לוגיקת ניקוי: מחיקת תפקידים קיימים (במידה ואין אילוצי מפתח זר)
        # אם יש כבר סטודנטים רשומים למשרות, השורה הזו עלולה להיכשל - וזה בסדר (היא תעבור ל-catch)
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
            
            # בדיקה אם התפקיד קיים (למקרה שהמחיקה למעלה נכשלה עקב אילוצי DB)
            existing_role = db.query(models.JobRole).filter(models.JobRole.title == title).first()
            
            if not existing_role:
                new_role = models.JobRole(title=title, demand_level=demand)
                db.add(new_role)
                added_count += 1
                
        db.commit()
        
        return {
            "message": "Market roles synchronized successfully",
            "added_new_roles": added_count,
            "roles_from_ai": ai_roles
        }

    except Exception as e:
        db.rollback()
        print(f"AI Sync Error: {e}")
        raise HTTPException(status_code=500, detail=f"Claude AI Sync failed: {str(e)}")
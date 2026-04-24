import re
from sqlalchemy.orm import Session
import crud

def get_recommendations(db: Session, student_id: int):
    courses = crud.get_courses(db)
    history = crud.get_student_history(db, student_id)
    profile = crud.get_student_profile(db, student_id)
    
    passed_course_codes = {h.course_code for h in history if h.grade >= 60}
    
    # Career/track preferences
    interested_track_ids = {t.id for t in profile.interested_tracks}
    interested_job_roles = profile.interested_job_roles
    
    target_role_names = [jr.title for jr in interested_job_roles]
    target_skill_ids = {s.id for jr in interested_job_roles for s in jr.skills}
    
    recommended_courses = []
    
    for course in courses:
        # Exclusion Rules
        if course.course_code in passed_course_codes:
            continue
            
        if course.prerequisites:
            prereq_codes = [int(p) for p in re.findall(r'\d{4,5}', course.prerequisites)]
            if prereq_codes and not all(p in passed_course_codes for p in prereq_codes):
                continue
                
        # Scoring logic
        score = 0
        
        # 1. Role Alignment (35%)
        course_skill_ids = {s.id for s in course.skills}
        if course_skill_ids & target_skill_ids:
            score += 35
            
        # 2. Track Match (25%)
        if course.track_id and course.track_id in interested_track_ids:
            score += 25
            
        # 3. Skill Contribution (20%)
        if course.skills:
            score += min(20, len(course.skills) * 5)
            
        # 4. Peer Reviews (10%)
        reviews = crud.get_course_reviews(db, course.course_code)
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            score += int(avg_rating * 2) # 5 stars = 10 points
        else:
            score += 6 # default 3 stars = 6 points
            
        # 5. Personal Constraints (10%)
        if profile.target_workload >= course.workload:
            score += 5
        if not profile.needs_flexible_attendance or not course.mandatory_attendance:
            score += 5
            
        # Explanation Rule:
        # "This course is recommended because it boosts your [Skill X] and aligns with your goal of becoming a [Role Y]."
        course_skill_names = [s.name for s in course.skills]
        top_skill = course_skill_names[0] if course_skill_names else "Technical Knowledge"
        target_role = target_role_names[0] if target_role_names else "Professional"
        
        explanation = f"This course is recommended because it boosts your {top_skill} and aligns with your goal of becoming a {target_role}."
        
        # Only add to recommendations if there is some merit
        if score > 0:
            recommended_courses.append({
                "course": course,
                "score": score,
                "explanation": explanation
            })
        
    # Sort by score descending
    recommended_courses.sort(key=lambda x: x["score"], reverse=True)
    
    return recommended_courses

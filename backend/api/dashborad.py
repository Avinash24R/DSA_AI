from fastapi import APIRouter, HTTPException

from Tools.student_tools import (
    get_user_progress,
    get_weak_topics,
    get_recent_attempts,
    get_skill_profile,
)

from Tools.roadmap_tools import (
    get_roadmap,
)

from Tools.problem_tools import (
    get_problem,
)

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)
@router.get("")
def dashboard(user_id: int):
    try:
        progress = get_user_progress(
            user_id,
            None
        )
        weak_topics = get_weak_topics(
            user_id
        )
        recent_attempts = get_recent_attempts(
            user_id
        )
        skill_profile = get_skill_profile(
            user_id
        )
        return {
            "progress": progress,
            "weak_topics": weak_topics,
            "recent_attempts": recent_attempts,
            "skill_profile": skill_profile,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
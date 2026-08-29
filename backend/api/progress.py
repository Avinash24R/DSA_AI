from fastapi import APIRouter, HTTPException

from Tools.student_tools import (
    get_user_progress,
    get_skill_profile,
)
router = APIRouter(
    prefix="/api/progress",
    tags=["Progress"]
)
@router.get("")
def progress(user_id: int):
    try:
        return {
            "progress": get_user_progress(
                user_id,
                None
            ),
            "skill_profile": get_skill_profile(
                user_id
            ),
        }
    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
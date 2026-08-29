from fastapi import APIRouter, HTTPException

from Tools.roadmap_tools import (
    get_roadmap,
)

router = APIRouter(
    prefix="/api/roadmap",
    tags=["Roadmap"]
)

@router.get("")
def roadmap():
    try:
        return {
            "topics": get_roadmap()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
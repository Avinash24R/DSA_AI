from fastapi import APIRouter, HTTPException

from backend.schemas.submission import CodeSubmission

from backend.services.agent_service import (
    start_session,
    get_current_session,
    submit_solution,
)
router = APIRouter(
    prefix="/api/agent",
    tags=["Agent"])

@router.post("/session/start")
def start(user_id: int):
    try:
        return start_session(
            user_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@router.get(
    "/session/{thread_id}/current"
)
def current(thread_id: str):
    try:
        return get_current_session(
            thread_id
        )
    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get(
    "/session/current"
)
def current_demo():
    # Lightweight demo response for the frontend when LangGraph isn't running.
    return {
        "thread_id": "guest",
        "user": {
            "name": "Demo Student",
            "level": "Beginner",
            "streak": 1,
            "xp": 100,
            "accuracy": 0
        },
        "task": {
            "problem_id": "demo:1",
            "title": "Sum of Numbers",
            "topic": "Arrays",
            "subtopic": "Basics",
            "difficulty": "Easy",
            "url": "#",
            "estimated_minutes": 15,
            "attempt_number": 1
        },
        "skill": {
            "score": 10,
            "solved": 0,
            "attempts": 0,
            "accuracy": 0
        }
    }
@router.post(
    "/session/{thread_id}/submit"
)
async def submit(
    thread_id: str,
    submission: CodeSubmission
):
    try:
        return await submit_solution(
            thread_id=thread_id,
            code=submission.code,
            language=submission.language
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from scripts.setup import get_connection
from Agent.graph import graph
from langchain_core.runnables import RunnableConfig
from typing import Any, Mapping, cast
from langgraph.types import Command
from backend.schemas.submission import CodeSubmission
from backend.services.agent_service import (
    start_session,
    get_current_session,
    submit_solution,
)
from backend.services.codeforces_service import (
    check_codeforces_submission,
    get_problem_assignment
)
from backend.services.leetcode_service import check_leetcode_submission

class SessionStartRequest(BaseModel):
    user_id: int


router = APIRouter(
    prefix="/api/agent",
    tags=["Agent"])

@router.post("/session/start")
def start(
    user_id: int | None = Query(default=None),
    payload: SessionStartRequest | None = None,
):
    resolved_user_id = user_id if user_id is not None else (payload.user_id if payload else None)

    if resolved_user_id is None:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        return start_session(resolved_user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@router.get("/session/{thread_id}/current")
def current(thread_id: str):
    try:
        return get_current_session(thread_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@router.post("/session/{thread_id}/submit")
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
            detail=str(e))
@router.post("/session/{thread_id}/check-submission")
async def check_submission(thread_id : str):
    config = cast(RunnableConfig, {
        "configurable": {
            "thread_id": thread_id
        }
    })
    try:
        state = graph.get_state(config)
        if not state or not state.values:
            raise ValueError("Agent session not found")
        current_state = state.values
        problem = current_state.get("current_problem")
        if not problem:
            raise ValueError("No active problem")

        source = problem.get("source")
        if source not in ("codeforces", "leetcode"):
            raise ValueError(f"Unsupported problem source: {source}")

        user_id = current_state.get("user_id")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT codeforces_handle, leetcode_handle
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,)
                )
                row = cur.fetchone()
        if not row:
            raise ValueError("User not found")

        if isinstance(row, dict):
            codeforces_handle = row["codeforces_handle"] # type: ignore
            leetcode_handle = row["leetcode_handle"] # type: ignore
        else:
            codeforces_handle = row[0]
            leetcode_handle = row[1]

        assigment_id = current_state.get("problem_assignment_id")
        if not assigment_id:
            raise ValueError("No active problem assignment")
        assignment = get_problem_assignment(assigment_id) # type: ignore
        if not assignment:
            raise ValueError("Problem assigment not found")
        assigned_at = assignment["assigned_at"]

        metadata = problem.get("metadata" , {}) or {}

        if source == "codeforces":
            if not codeforces_handle:
                raise ValueError("Codeforces handle is not configured")

            problem_index = metadata.get("index")
            contest_id = metadata.get("contest_id")
            if contest_id is None or not problem_index:
                raise ValueError("Codeforces problem metadata is incomplete")

            judge_res = check_codeforces_submission(
                handle=codeforces_handle,
                contest_id=contest_id,
                problem_index=problem_index,
                assigned_at=assigned_at,
            )
        else:
            if not leetcode_handle:
                raise ValueError("LeetCode handle is not configured")

            slug = metadata.get("slug")
            if not slug:
                raise ValueError("LeetCode problem metadata is incomplete")

            judge_res = check_leetcode_submission(
                handle=leetcode_handle,
                slug=slug,
                assigned_at=assigned_at,
            )

        if not judge_res["found"]:
            return {
                "status": "not_found",
                "judge_result": judge_res,
                "message": (
                    f"No accepted {source} submission found yet."
                ),
            }
        res = graph.invoke(
            Command(
                resume={
                    "user_answer": "",
                    "judge_result": judge_res
                }
            ),
            config=config
        )
        return {
            "status": (
                "accepted"
                if judge_res["accepted"]
                else "rejected"
            ),

            "judge_result": judge_res,

            "next_action": res.get(
                "next_action",
                "EVALUATE"
            ),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
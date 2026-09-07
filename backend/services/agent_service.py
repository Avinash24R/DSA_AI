from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from typing import cast
from Agent.state import DSAState
from Agent.graph import graph
from Tools.problem_tools import get_problem
from Tools.problem_tools import get_test_cases
from Tools.student_tools import get_user_by_id, get_skill_profile

from .judge_service import run_code
import uuid

def get_config(thread_id : str):
    return cast(RunnableConfig, {
        "configurable": {
            "thread_id": thread_id
        }
    })
def start_session(user_id: int):
    thread_id = f"user-{user_id}--{uuid.uuid4()}"
    config = get_config(thread_id)

    state :DSAState ={
        "user_id" : user_id
    }
    try : 
        result = graph.invoke(
            state,
            config=config
        )
    except Exception as e:
        print(f"START SESSION ERROR : {type(e).__name__}: {e}")
        raise
    return {
        "thread_id": thread_id,
        "user_id" : user_id,
        "state": result
    }

def _build_skill_summary(user_id):
    """
    DSAState never carries a "user" or "skill" key, so the
    old code always returned {} for both and the UI silently
    showed placeholder data. Build a real aggregate from the
    roadmap-wide skill profile instead.
    """
    profile = get_skill_profile(user_id) if user_id else []

    total_solved = sum(t.get("problems_solved") or 0 for t in profile)
    total_attempted = sum(t.get("problems_attempted") or 0 for t in profile)

    attempted_topics = [t for t in profile if (t.get("problems_attempted") or 0) > 0]
    avg_skill_score = (
        sum(float(t.get("skill_score") or 0) for t in attempted_topics)
        / len(attempted_topics)
        if attempted_topics
        else 0
    )

    accuracy = (
        round((total_solved / total_attempted) * 100, 1)
        if total_attempted
        else 0
    )

    return {
        "score": round(avg_skill_score, 1),
        "solved": total_solved,
        "attempts": total_attempted,
        "accuracy": accuracy,
        "topics": profile,
    }

def get_current_session(thread_id: str):
    config = get_config(thread_id)
    state = graph.get_state(config)

    if not state or not state.values:
        raise ValueError("Session not found")
    
    values = state.values
    user_id = values.get("user_id")

    task = values.get("current_problem") or None
    if task:
        task = {
            **task,
            "attempt_number": values.get("attempt_number", 1),
            "subtopic": (task.get("topics") or [None])[0],
        }

    return  {
        "thread_id":thread_id,
        "user": get_user_by_id(user_id) if user_id else None,
        "skill": _build_skill_summary(user_id),
        "topic":{
            "id": values.get("current_topic_id"),
            "name": (
                values.get("current_topic")
                or values.get("topic")
            ),
            "summary": (
                values.get("topic_summary")
                or values.get("lesson")
            ),
        },
        "topic_summary": (
            values.get("topic_summary")
            or values.get("lesson")
        ),
        "task": task,
        "next_action":values.get("next_action"),
    }

async def submit_solution(thread_id:str, code:str, language: str):
    config = get_config(thread_id)

    state = graph.get_state(config).values

    problem = state.get(
        "current_problem"
    )

    if not problem:
        raise ValueError(
            "No active problem"
        )

    problem_db_id = problem["id"]

    test_cases = get_test_cases(
        problem_db_id
    )
    if not test_cases:
        raise ValueError("No test case Configured for this problem")
    judge_result = await run_code(
        code=code,
        language=language,
        test_cases=test_cases
    )
    result = graph.invoke(
        Command(
            resume={
                "code":code,
                "judge_result": judge_result
            }
        ),
        config= config
    )
    return result
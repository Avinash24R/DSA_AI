from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from typing import cast
from Agent.state import DSAState
from Agent.graph import graph
from Tools.problem_tools import get_problem
from Tools.problem_tools import get_test_cases

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
def get_current_session(thread_id: str):
    config = get_config(thread_id)
    state = graph.get_state(config)

    if not state or not state.values:
        raise ValueError("Session not found")
    
    values = state.values
    return  {
        "thread_id":thread_id,
        "user":values.get("user"),
        "skill":values.get("skill"),
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
        "task":values.get("current_problem"),
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
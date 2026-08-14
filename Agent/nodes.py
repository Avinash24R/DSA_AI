from state import DSAState
import os
from pathlib import Path
from dotenv import load_dotenv
from Tools.student_tools import *
from Tools.problem_tools import *
from Tools.roadmap_tools import *
from Tools.Eval_tools import *
import time

from langchain_groq import ChatGroq
from langgraph.types import interrupt

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

groq_api_key = os.getenv("GROQ_API")
if not groq_api_key:
    raise RuntimeError("Missing GROQ_API in the environment or .env file.")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    api_key=groq_api_key, # type: ignore
)

def load_student(state: DSAState) -> DSAState:
    """
    Load the student's persistent data from PostgreSQL
    into the LangGraph state.
    """

    user_id = state.get("user_id")

    if not user_id:
        raise ValueError(
            "user_id must be provided in state"
        )

    # Load student data from PostgreSQL
    progress = get_user_progress(user_id , state.get("current_topic_id"))

    weak_topics = get_weak_topics(user_id)

    recent_attempts = get_recent_attempts(user_id)

    skill_profile = get_skill_profile(user_id)

    # Update existing state.
    # Do NOT create a new DSAState here.
    state["progress"] = progress # type: ignore
    state["weak_topics"] = weak_topics
    state["recent_attempts"] = recent_attempts # type: ignore
    state["skill_profile"] = skill_profile # type: ignore

    return state
def evaluate_skill(state: DSAState) -> DSAState:
    """
    Evaluate the student's current DSA skill.
    """

    user_id = state.get("user_id")

    if not user_id:
        raise ValueError("user_id must be provided")

    weak_topics = state.get("weak_topics", [])
    recent_attempts = state.get("recent_attempts", [])
    skill_profile = state.get("skill_profile", [])
    progress = state.get("progress", [])

    scores = [
        float(topic["skill_score"])
        for topic in skill_profile
        if topic.get("skill_score") is not None
    ]

    avg_score = sum(scores) / len(scores) if scores else 0

    if avg_score < 40:
        level = "beginner"
    elif avg_score < 70:
        level = "intermediate"
    else:
        level = "advanced"

    weakest_topic = None

    if weak_topics:
        weakest_topic = min(
            weak_topics,
            key=lambda x: float(x.get("skill_score", 100))
        )

    state["skill_evaluation"] = {
        "overall_level": level,
        "weakest_topic": weakest_topic,
        "average_skill_score": avg_score,
        "progress": progress,
        "recent_attempts": recent_attempts,
    }

    return state
def select_topic(state: DSAState) -> DSAState:

    """
    Select the next roadmap topic.
    """

    user_id = state.get("user_id")

    if not user_id:
        raise ValueError("user_id must be provided")

    evaluation = state.get("skill_evaluation", {})

    weakest_topic = evaluation.get("weakest_topic")

    if weakest_topic:
        topic_id = weakest_topic["roadmap_topic_id"]

    else:
        topic = get_next_topic(user_id)

        if not topic:
            raise ValueError("No next topic available")

        topic_id = topic["id"]

    topic = get_topic(topic_id)

    if not topic:
        raise ValueError(
            f"Roadmap topic {topic_id} does not exist"
        )

    children = get_children(topic_id)

    state["current_topic_id"] = topic["id"]
    state["current_topic"] = topic["name"]
    state["available_subtopics"] = children # type: ignore
    state["next_action"] = "TEACH_TOPIC"

    return state
def teach_topic(state:DSAState) -> DSAState:
    topic = state.get("current_topic")
    subtopic = state.get("available_subtopics" , [])
    skill = state.get("skill_evaluation", {})

    prompt = f"""
    You are a DSA mentor teaching C++

    Topic:
    {topic}

    Subtopic:
    {subtopic}

    Student skill:
    {skill}

    Teach this topic so the student can recognize and solve
DSA problems involving this pattern.

Include:
1. Core concept
2. Internal intuition
3. Pattern recognition
4. C++ example
5. Time and space complexity
6. Common mistakes
7. Eaxmple code

Do not give a practice problem yet.
"""
    
    response = llm.invoke(prompt)
    state["lesson"] = response.content
    state["next_action"] = "SELECT_PROBLEM"

    return state

def select_problem_node(state: DSAState) -> DSAState:
    topic_id = state.get("current_problem_id")

    skill = state.get("skill_evaluation", {})

    recent_attempts = state.get("recent_attempts", [])

    problem = select_problem(
        topic_id=topic_id,
        skill=skill,
        recent_attempts=recent_attempts,
    )

    if not problem:
        raise ValueError("No suitable problem found")

    state["current_problem_id"] = problem["problem_id"]
    state["current_problem"] = problem
    state["attempt_number"] = 1
    state["hint_level"] = 0

    state["next_action"] = "PRESENT_PROBLEM"

    return state
def present_problem(state: DSAState) -> DSAState:

    problem = state.get("current_problem")

    state.get("thinking_start_time") = time.time() # type: ignore

    state["next_action"] = "AWAIT_SUBMISSION"

    return state
def wait_for_user(state: DSAState)-> DSAState:
    answer = interrupt({
        "type": "code_submission",
        "problem_id": state.get("current_problem_id"),
        "message": "Submit your c++ solution"
    })

    state["user_answer"] = answer
    state["next_action"] = "EVALUATE"

    return state

def evaluate_answer(state: DSAState) -> DSAState:

    evaluation = evaluate_submission(
        problem=state.get("current_problem"),
        answer=state.get("user_answer"),
        thinking_time=state.get("thinking_time_seconds", 0),
    )

    state["evaluation"] = evaluation # type: ignore

    if evaluation["correct"]:
        state["next_action"] = "UPDATE_PROGRESS"
    else:
        state["next_action"] = "HINT_RETRY"

    return state

def hint_retry(state: DSAState) -> DSAState:
    '''
    later 
    wrong answer
    ↓
analyze mistake
    ↓
generate appropriate hint
    ↓
WAIT_FOR_USER
    '''
    state["hint_level"] = state.get("hint_level", 0) + 1

    state["next_action"] = "WAIT_FOR_USER"

    return state
def update_progress_node(state: DSAState) -> DSAState:

    save_attempt(
        user_id=state.get("user_id"),
        roadmap_topic_id=state.get("current_topic_id"),
        problem_id=state.get("current_problem_id"),
        attempt_number=state.get("attempt_number"),
        thinking_time_seconds=state.get(
            "thinking_time_seconds", 0
        ),
        evaluation=state.get("evaluation"),
    )

    update_progress(
        user_id=state.get("user_id"),
        roadmap_topic_id=state.get("current_topic_id"),
        evaluation=state.get("evaluation"),
    )

    state["next_action"] = "END"

    return state
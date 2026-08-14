from typing import TypedDict, Optional
# the roadmap , all attempts , user progress is in db just need the data that is current needed
'''
skill eavluation
{
    "overall_level": "intermediate",
    "weak_topics": [...],
    "strong_topics": [...],
    "recommended_topic_id": 12,
    "reason": "...",
    "confidence": 0.87
}
'''
from typing import TypedDict, Optional, Any


class DSAState(TypedDict, total=False):
    # Student
    user_id: int

    progress: list[dict[str, Any]]
    weak_topics: list[dict[str, Any]]
    recent_attempts: list[dict[str, Any]]
    skill_profile: list[dict[str, Any]]

    # Skill evaluation
    skill_evaluation: dict[str, Any]

    # Current roadmap position
    current_topic_id: int
    current_topic: str
    available_subtopics: list[dict[str, Any]]

    # Current problem
    current_problem_id: str
    current_problem: dict[str, Any]


    # Problem session
    attempt_number: int
    hint_level: int
    thinking_time_seconds: int
    thinking_start_time : float
    user_answer: str

    # Evaluatio2
    evaluation: dict[str, Any]

    # Workflow control
    lesson: str |  list[str | dict[Any, Any]]
    next_action: str

    
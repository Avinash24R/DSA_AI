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
from pydantic import BaseModel , Field


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

    #problems
    problem_pool_ready: bool
    problem_pool_count: int


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
    judge_result: dict[str, Any]
    evaluation: dict[str, Any]

    # Workflow control
    lesson: str |  list[str | dict[Any, Any]]
    next_action: str

class SubmissionEvaluation(BaseModel):
    problem_title: str
    problem_source: str
    difficulty: str

    correct: bool

    code_quality_score: float = Field(ge=0, le=10)
    approach_score: float = Field(ge=0, le=10)
    complexity_score: float = Field(ge=0, le=10)

    overall_score: float = Field(ge=0, le=100)

    time_complexity: str
    space_complexity: str

    identified_pattern: Optional[str] = None
    expected_pattern: Optional[str] = None

    mistakes: list[str] = []
    edge_cases_missed: list[str] = []

    feedback: str

class ProblemSelection(BaseModel):
    problem_id: str
    reason: str
class Problem(BaseModel):
    problem_id: str
    source: str
    title: str
    difficulty: str
    topics: list[str]
    url: str
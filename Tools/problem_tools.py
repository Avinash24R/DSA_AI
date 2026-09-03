'''
Problem Tools
────────────────────────

get_problem(problem_id)
find_problems(...)
select_problem(...)

Todo :
DB/API
 ↓
filter:
  topic
  difficulty
  unsolved
  weak pattern
  previous attempts
 ↓
20 candidate problems
 ↓
LLM
 ↓
1 problem_id
 ↓
get_problem()
 ↓
present to student
'''
from typing import Any, cast
from Agent.llm import get_llm
try:
    from Agent.state import ProblemSelection
except ImportError:  # pragma: no cover
    from Agent.state import ProblemSelection

from scripts.setup import get_connection

def get_problem(problem_id: str) -> dict[str, Any] | None:

    source, external_id = problem_id.split(":", 1)

    query = """
        SELECT
            id,
            source,
            external_id,
            title,
            difficulty,
            url,
            description,
            topics,
            metadata
        FROM problems
        WHERE
            source = %s
            AND external_id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (source, external_id),
            )

            row = cur.fetchone()

            return dict(row) if row else None
    return None
def find_problems(topic_id: int, topic_name: str, difficulty: str | None, limit: int = 20) -> list[dict[str, Any]]:
    '''
    Search problems for a roadmap topic from the local DB.
    '''
    query = """
        SELECT
            p.id AS problem_id,
            p.source,
            p.external_id,
            p.title,
            p.difficulty,
            p.url,
            p.topics
        FROM problems p
        JOIN problem_topics pt
            ON pt.problem_id = p.id
        WHERE
            pt.roadmap_topic_id = %s
            AND p.difficulty = %s
        LIMIT %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (topic_id, difficulty, limit))
            return [dict(row) for row in cur.fetchall()]


def select_problem(topic_id:int, topic_name:str, skill:dict[str, Any], recent_attempts:list[dict[str, Any]], limit=20):
    '''
    1. get candidate problems
    2.remove recept attempted problems.
    3.Give candidate + student context to llm
    4. LLM return one problem id
    '''
    difficulty = (skill.get("target_difficulty", "easy") or "easy").strip().lower()
    candidates = find_problems(
        topic_id=topic_id,
        topic_name=topic_name,
        difficulty=difficulty,
        limit=limit,
    )
    if not candidates:
        raise ValueError("No candidate problems found")
    attempted_ids = {
        attempt["problem_id"]
        for attempt in recent_attempts
        if attempt.get("problem_id")
    }
    candidates = [
        problem
        for problem in candidates
        if problem["problem_id"] not in attempted_ids
    ]
    if not candidates:
        raise ValueError(
            "All candidate problems were already attempted"
        )
    candidate_context = [
        {
            "problem_id": f'{problem["source"]}:{problem["external_id"]}',
            "title": problem["title"],
            "difficulty": problem["difficulty"],
            "topics": problem["topics"],
        }
        for problem in candidates[:20]
    ]
    prompt = f"""
    You are a DSA problem selector.

    Student skill:
    {skill}

    Current roadmap topic:
    {topic_name}

    Recent attempts:
    {recent_attempts}

    Candidate problems:
    {candidate_context}

    Select exactly ONE problem.

    Choose the problem that best matches:
    - current topic
    - student's skill level
    - weaknesses
    - previous attempts

    Return only the selected problem_id and a short reason.

    Return valid JSON matching the schema exactly.
    Boolean fields must be JSON booleans: true or false, not strings.
    Numeric fields must be numbers, not strings.
    Do not return Python syntax
    """
    llm = get_llm()

    structured_llm = llm.with_structured_output(
        ProblemSelection,
        method="json_schema",
    )

    selection = structured_llm.invoke(prompt)

    if not isinstance(selection, ProblemSelection):
        raise TypeError(
            f"Expected ProblemSelection, got {type(selection).__name__}"
        )

    return selection.problem_id
def get_test_cases(problem_id: int):
    query = """
        SELECT
            input,
            expected_output
        FROM problem_test_cases
        WHERE problem_id = %s
        ORDER BY id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                query,
                (problem_id,)
            )

            return [
                dict(row)
                for row in cur.fetchall()
            ]
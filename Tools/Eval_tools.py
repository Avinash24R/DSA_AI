'''

Evaluation Tools
────────────────────────

save_attempt(...)
update_progress(...)
'''
from scripts.setup import get_connection
from Agent.state import SubmissionEvaluation
from typing import cast
from Agent.llm import get_llm
import json
def save_attempt(user_id,roadmap_topic_id , problem_id, attempt_number, thinking_time_seconds ,evaluation):
    '''
    Persist one problem attempt into problem_attempts table.
    '''

    query = """
        INSERT INTO problem_attempts (
            user_id,
            roadmap_topic_id,
            problem_source,
            problem_id,
            problem_title,
            difficulty,
            attempt_number,
            thinking_time_seconds,
            submission_time_seconds,
            correct,
            time_complexity,
            space_complexity,
            approach_score,
            code_quality_score,
            complexity_score,
            overall_score,
            evaluation
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        );

    """

    params = (
        user_id,
        roadmap_topic_id,

        evaluation.get("problem_source", "leetcode"),
        problem_id,
        evaluation.get("problem_title"),
        evaluation.get("difficulty"),

        attempt_number,
        thinking_time_seconds,
        evaluation.get("submission_time_seconds"),

        evaluation.get("correct"),

        evaluation.get("time_complexity"),
        evaluation.get("space_complexity"),

        evaluation.get("approach_score"),
        evaluation.get("code_quality_score"),
        evaluation.get("complexity_score"),
        evaluation.get("overall_score"),

        json.dumps(evaluation),
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query , params)
        conn.commit()
def create_problem_assignment(
    user_id: int | None,
    problem_id: int | None,
) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO problem_assignments (
                    user_id,
                    problem_id
                )
                VALUES (%s, %s)
                RETURNING id;
                """,
                (
                    user_id,
                    problem_id,
                ),
            )
            row = cur.fetchone()
        conn.commit()
    if isinstance(row, dict):
        return row["id"] # type: ignore
    return row[0]

def complete_problem_assignment(
    assignment_id: int,
    submission_id: int,
    submitted_at,
) -> None:

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE problem_assignments
                SET
                    submitted_at = %s,
                    codeforces_submission_id = %s,
                    status = 'submitted'
                WHERE id = %s
                """,
                (
                    submitted_at,
                    submission_id,
                    assignment_id,
                ),
            )

        conn.commit()

def update_progress(user_id ,roadmap_topic_id ,evaluation , thinking_time_seconds):
    '''
    Update aggregate user progress.

    latter todo better sccoring straegy
    correctness
    + approach
    + complexity
    + thinking time
    + difficulty
    + attempt number
    + pattern recognition
    + historical performance 
    '''
    query = """
        INSERT INTO user_progress (
            user_id,
            roadmap_topic_id,
            skill_score,
            weak_score,
            problems_attempted,
            problems_solved,
            avg_thinking_time_seconds,
            last_attempted_at
        )
        VALUES (
            %s, %s, %s, %s, 1, %s, %s, NOW()
        )
        ON CONFLICT (user_id, roadmap_topic_id)
        DO UPDATE SET

            skill_score =
                (
                    user_progress.skill_score * 0.7
                    +
                    EXCLUDED.skill_score * 0.3
                ),

            weak_score =
                EXCLUDED.weak_score,

            problems_attempted =
                user_progress.problems_attempted + 1,

            problems_solved =
                user_progress.problems_solved
                + EXCLUDED.problems_solved,
            avg_thinking_time_seconds =
                CASE
                    WHEN EXCLUDED.avg_thinking_time_seconds IS NULL
                    THEN user_progress.avg_thinking_time_seconds

                    WHEN user_progress.avg_thinking_time_seconds IS NULL
                    THEN EXCLUDED.avg_thinking_time_seconds

                    ELSE (
                        user_progress.avg_thinking_time_seconds
                        +
                        EXCLUDED.avg_thinking_time_seconds
                    ) / 2
                END,

            last_attempted_at = NOW();
    
    """
    overall_score = float(evaluation.get("overall_score", 0))

    correct = bool(evaluation.get("correct", False))

    weak_score = max(0, 100 - overall_score)
    params = (
        user_id,
        roadmap_topic_id,
        overall_score,
        weak_score,
        1 if correct else 0,
        thinking_time_seconds,
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)

        conn.commit()
def evaluate_submission(problem , answer , judge_result,  thinking_time):
    '''
    judge_result -> whatever come from the  api of codefroce and leetcode.
    accepted / wrong answer / TLE / runtime error / compilation error
    {
    "problem_title" : "house robber",
    "problem_source" :"leetcode",
    "correct": True,
    "difficulty" : "hard",
    "submission_time_secode" : "12:23:20",
    "code_quality_score": 7.5,
    "approach_score": 8,
    "complexity_score": 9,
    "overall_score": 85,
    "Time_Complexity: "O(n)",
    "Space_Complexity: "O(n)",
    "feedback": "Correct sliding window approach."
}
    '''

    llm = get_llm()
    structured_llm = llm.with_structured_output(
        SubmissionEvaluation,
        method="json_schema",
    )
    prompt = f"""
        You are an expert competitive programming evaluator.

        Evaluate the student's solution.

        PROBLEM:
        {problem}

        STUDENT C++ CODE:
        {answer}

        JUDGE RESULT:
        {judge_result}

        THINKING TIME:
        {thinking_time} seconds

        Evaluate:

        1. Correctness
        2. Algorithmic approach
        3. Pattern recognition
        4. Time complexity
        5. Space complexity
        6. Code quality
        7. Edge cases
        8. Overall DSA understanding

        Important:
        - Do not blindly trust the student's claimed complexity.
        - Derive complexity from the actual code.
        - Use the judge result when determining correctness.
        - Identify the DSA pattern used.
        - Compare it with the expected pattern.
        - Give actionable feedback.

        Return valid JSON matching the schema exactly.
        Boolean fields must be JSON booleans: true or false, not strings.
        Numeric fields must be numbers, not strings.
        Do not return Python syntax

    """

    res = structured_llm.invoke(prompt)
    if not isinstance(res, SubmissionEvaluation):
        raise TypeError(
                f"Expected ProblemSelection, got {type(res).__name__}"
            )
    return res.model_dump()
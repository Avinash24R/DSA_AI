"""
Hint / chat-with-AI generation.

Deliberately kept OUTSIDE the LangGraph pipeline in Agent/nodes.py:
a hint request happens while the student is still parked at
wait_for_user()'s interrupt(), and resuming that interrupt requires a
final judge_result - a hint isn't a submission, so it must not
advance (or require resuming) the graph. This talks to the LLM and to
Postgres directly, reading the student's current state read-only via
graph.get_state().
"""

from .llm import get_llm

MAX_HINTS_PER_PROBLEM = 5


def _reveal_guidance(hint_number: int) -> str:
    """
    Escalating instructions for how much of the solution a hint at
    this level is allowed to show. Deliberately never reaches "give
    the full solution" - even at the last hint, at least one
    meaningful piece must be left for the student to write themselves.
    """
    if hint_number <= 1:
        return """
This is hint 1 of 5. Give ONLY a conceptual nudge:
- Name the pattern/data structure/technique that applies (e.g. "this
  is a sliding window problem" or "think about a hash map for O(1)
  lookups").
- Do NOT write any code, even pseudocode.
- Do NOT describe the algorithm step by step yet.
"""
    if hint_number == 2:
        return """
This is hint 2 of 5. Explain the APPROACH in plain English:
- Walk through the algorithm's steps conceptually.
- You may reference variable roles in words (e.g. "a pointer that
  tracks the window's start").
- Still do NOT write actual code or pseudocode.
"""
    if hint_number == 3:
        return """
This is hint 3 of 5. Give a code SKELETON, roughly 30-40% filled in:
- Function signature, variable declarations, and loop/condition
  structure can be real code.
- Replace the core algorithmic logic with clear `// TODO: ...`
  comments describing what needs to go there.
- Do NOT fill in the TODOs yourself.
"""
    if hint_number == 4:
        return """
This is hint 4 of 5. Give a MORE COMPLETE skeleton, roughly 60-70%
filled in:
- Most boilerplate (loops, variable setup, edge case checks) can now
  be real, working code.
- The single most important algorithmic step (the actual transition,
  comparison, or formula that solves the problem) must STILL be a
  `// TODO: ...` comment, not real code.
"""
    return """
This is hint 5 of 5 - the LAST hint for this problem. Give the most
complete help you will ever give here, but you must STILL leave
exactly one meaningful piece unfinished:
- Nearly all of the code can be real and correct.
- Deliberately leave ONE critical line, expression, or function body
  as a `// TODO: complete this` (e.g. the final return expression, or
  the one key recurrence/comparison).
- Explicitly tell the student this is their last hint and they need
  to complete that final piece themselves.
- Under no circumstances output a fully complete, directly runnable
  solution - even now.
"""


def generate_hint(
    problem: dict,
    skill: dict,
    chat_history: list[dict],
    hint_number: int,
    user_message: str | None,
) -> str:
    """
    Returns the assistant's reply text for one hint/chat turn.

    problem: the current_problem dict (title, description, difficulty, ...)
    skill: state["skill_evaluation"] (overall level, target difficulty, ...)
    chat_history: prior turns for this assignment, oldest first, each
        like {"role": "user"|"assistant", "content": "..."}
    hint_number: 1-5, which hint slot this reply fills
    user_message: the student's free-text question, or None/"" if they
        just clicked "Get a hint" with no specific question
    """

    history_text = "\n".join(
        f"{turn['role'].upper()}: {turn['content']}" for turn in chat_history
    ) or "(no previous messages)"

    question = user_message.strip() if user_message else (
        "(The student didn't type anything specific - they just asked for a hint.)"
    )

    prompt = f"""
You are a patient DSA mentor helping a student who is stuck on a
problem. You are NOT a solution generator - your job is to guide,
not to solve it for them.

PROBLEM:
{problem}

STUDENT SKILL:
{skill}

CONVERSATION SO FAR (for this problem):
{history_text}

STUDENT'S MESSAGE:
{question}

{_reveal_guidance(hint_number)}

Universal rules, no matter the hint number:
- Never reveal a complete, directly runnable solution.
- Tailor your explanation to the student's stated skill level.
- If the student's message shows a specific misunderstanding, address
  that directly rather than giving a generic hint.
- Keep it concise - a few sentences plus code/pseudocode where the
  hint level calls for it, not a full lecture.
- Respond in plain text/Markdown, not JSON.
"""

    llm = get_llm()
    response = llm.invoke(prompt)
    return response.content # type: ignore

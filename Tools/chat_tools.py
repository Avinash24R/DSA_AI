"""
Chat / hint persistence.

────────────────────────
get_hints_used(...)
increment_hints_used(...)
get_chat_history(...)
save_chat_message(...)
"""
from scripts.setup import get_connection


def get_hints_used(assignment_id: int | None) -> int:
    if assignment_id is None:
        return 0

    query = """
        SELECT hints_used
        FROM problem_assignments
        WHERE id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (assignment_id,))
            row = cur.fetchone()

    if not row:
        return 0
    return row["hints_used"] if isinstance(row, dict) else row[0]


def increment_hints_used(assignment_id: int | None) -> int:
    if assignment_id is None:
        return 0

    """
    Atomically bumps the counter and returns the new value, so a
    burst of near-simultaneous requests can't both slip past the
    5-hint cap.
    """
    query = """
        UPDATE problem_assignments
        SET hints_used = hints_used + 1
        WHERE id = %s
        RETURNING hints_used;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (assignment_id,))
            row = cur.fetchone()
        conn.commit()

    if not row:
        return 0
    return row["hints_used"] if isinstance(row, dict) else row[0]


def get_chat_history(assignment_id: int | None) -> list[dict]:
    if assignment_id is None:
        return []

    query = """
        SELECT role, content, hint_number, created_at
        FROM chat_messages
        WHERE problem_assignment_id = %s
        ORDER BY created_at ASC, id ASC;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (assignment_id,))
            rows = cur.fetchall()

    history = []
    for row in rows:
        if isinstance(row, dict):
            history.append(dict(row))
        else:
            history.append({
                "role": row[0],
                "content": row[1],
                "hint_number": row[2],
                "created_at": row[3],
            })
    return history


def save_chat_message(assignment_id: int | None, role: str, content: str, hint_number: int | None) -> None:
    if assignment_id is None:
        return

    query = """
        INSERT INTO chat_messages (problem_assignment_id, role, content, hint_number)
        VALUES (%s, %s, %s, %s);
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (assignment_id, role, content, hint_number))
        conn.commit()

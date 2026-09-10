'''
Student Tools
────────────────────────

get_user_progress(user_id)
get_weak_topics(user_id)
get_recent_attempts(user_id)
get_skill_profile(user_id)
'''
from scripts.setup import get_connection
from typing import List , Any 
from psycopg.rows import TupleRow
def get_user_progress(user_id : int , topic_id : int | None)-> list[TupleRow] | List[dict[str, Any]]:
    query = """
        SELECT 
            up.roadmap_topic_id,
            rt.name AS topic_name,
            rt.node_type,
            up.weak_score,
            up.problems_solved,
            up.problems_attempted,
            up.avg_thinking_time_seconds,
            up.last_attempted_at
        FROM user_progress up 
        JOIN roadmap_topics rt
            ON rt.id = up.roadmap_topic_id
        WHERE up.user_id = %s
    """
    params = [user_id]
    if topic_id is not None:
        query += """
         AND up.roadmap_topic_id = %s
        """
        params.append(topic_id)

    query += """
        ORDER BY rt.sequence_order;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
def get_weak_topics(user_id:int , threshold : float = 60.0)-> List[dict[str, Any]]:
    query = """
        SELECT
            up.roadmap_topic_id,
            rt.name AS topic_name,
            rt.node_type,
            up.skill_score,
            up.weak_score,
            up.problems_attempted,
            up.problems_solved,
            up.avg_thinking_time_seconds
        FROM user_progress up
        JOIN roadmap_topics rt
        ON rt.id = up.roadmap_topic_id
        WHERE up.user_id = %s
        AND up.skill_score < %s
        ORDER BY
            up.skill_score ASC,
            up.weak_score DESC;

    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id, threshold))
            return [dict(row) for row in cur.fetchall()]
def get_recent_attempts(user_id: int , limit = 10) -> List[dict[str, Any]]:
    query = """
        SELECT
            pa.id,
            pa.roadmap_topic_id,
            rt.name AS topic_name,
            pa.problem_source,
            pa.problem_id,
            pa.problem_title,
            pa.difficulty,
            pa.attempt_number,
            pa.thinking_time_seconds,
            pa.submission_time_seconds,
            pa.correct,
            pa.time_complexity,
            pa.space_complexity,
            pa.approach_score,
            pa.code_quality_score,
            pa.complexity_score,
            pa.overall_score,
            pa.evaluation,
            pa.created_at
        FROM problem_attempts pa

        LEFT JOIN roadmap_topics rt
        ON rt.id = pa.roadmap_topic_id
        WHERE pa.user_id = %s

        LIMIT %s; 


    """
    params = (user_id , limit)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    query = """
        SELECT
            id,
            name,
            email,
            level,
            codeforces_handle,
            leetcode_handle
        FROM users
        WHERE id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
def get_skill_profile(user_id)-> List[dict[str, Any]]:
    query = """
        SELECT
            rt.id AS roadmap_topic_id,
            rt.parent_id,
            rt.name AS topic_name,
            rt.node_type,
            rt.sequence_order,

            COALESCE(up.skill_score, 0) AS skill_score,
            COALESCE(up.weak_score, 0) AS weak_score,
            COALESCE(up.problems_attempted, 0) AS problems_attempted,
            COALESCE(up.problems_solved, 0) AS problems_solved,
            up.avg_thinking_time_seconds,
            up.last_attempted_at

        FROM roadmap_topics rt

        LEFT JOIN user_progress up
            ON up.roadmap_topic_id = rt.id
            AND up.user_id = %s

        ORDER BY
            rt.sequence_order,
            rt.id;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id,))
            return [dict(row) for row in cur.fetchall()]
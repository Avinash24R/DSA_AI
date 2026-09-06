from typing import Any, cast

from scripts.setup import get_connection
from .models import Problem
from psycopg.types.json import Jsonb


def save_problem(problem: Problem) -> int:
    
    query = """
        INSERT INTO problems (
            source,
            external_id,
            title,
            difficulty,
            url,
            topics,
            metadata
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )

        ON CONFLICT (source, external_id)
        DO UPDATE SET
            title = EXCLUDED.title,
            difficulty = EXCLUDED.difficulty,
            url = EXCLUDED.url,
            topics = EXCLUDED.topics,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()

        RETURNING id;
    """
    source = problem.source
    external_id = problem.problem_id.removeprefix(f"{problem.source}")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    source,
                    external_id,
                    problem.title,
                    problem.difficulty,
                    problem.url,
                    Jsonb(problem.topics),
                    Jsonb(problem.metadata),
                ),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("Problem insert did not return an ID")
            typed_row = cast(dict[str, Any], row)
            problem_id = typed_row["id"]
        conn.commit()
    return problem_id


def save_problem_topics(
    problem_id: int,
    topic_ids: list[int],
) -> None:
    if not topic_ids:
        return 
    query = """
        INSERT INTO problem_topics (
            problem_id,
            roadmap_topic_id
        )
        VALUES (%s, %s)
        ON CONFLICT (problem_id, roadmap_topic_id) DO NOTHING;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            for topic_id in topic_ids:
                cur.execute(
                    query,
                    (
                        problem_id,
                        topic_id,
                    ),
                )
        conn.commit()

def count_available_problems(
    topic_id: int,
    difficulty: str,
) -> int:

    query = """
        SELECT COUNT(*) AS count
        FROM problems p
        JOIN problem_topics pt
            ON pt.problem_id = p.id
        WHERE
            pt.roadmap_topic_id = %s
            AND p.difficulty = %s;
    """

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                (
                    topic_id,
                    difficulty,
                ),
            )

            row = cur.fetchone()
    return int(row["count"]) # type: ignore


def get_problem_count_by_topic(
    topic_id: int,
) -> int:

    query = """
        SELECT COUNT(*) AS count
        FROM problems p
        JOIN problem_topics pt
            ON pt.problem_id = p.id
        WHERE pt.roadmap_topic_id = %s;
    """

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                (topic_id,),
            )

            row = cur.fetchone()

    return int(row["count"]) # type: ignore
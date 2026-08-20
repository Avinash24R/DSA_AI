from typing import Any, cast

from scripts.setup import get_connection
from .models import Problem
from psycopg.types.json import Jsonb


def save_problem(problem: Problem) -> int:
    source = problem.source
    external_id = problem.problem_id.split(
        ":" , 1
    )[1]
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
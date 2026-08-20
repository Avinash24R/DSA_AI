'''
Roadmap Tools
────────────────────────

get_roadmap()
get_topic(topic_id)
get_children(topic_id)
get_next_topic(user_id)



'''
from typing import Any 
from scripts.setup import get_connection
def get_roadmap() -> list[dict[str, Any]]:
    query = """
        SELECT
            id,
            parent_id,
            name,
            node_type,
            sequence_order,
            description
        FROM roadmap_topics
        ORDER BY sequence_order, id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return [dict(row) for row in cur.fetchall()]
def get_topic(topic_id) -> dict[str, Any] | None:
    query = """
        SELECT
            id,
            parent_id,
            name,
            node_type,
            sequence_order,
            description
        FROM roadmap_topics
        WHERE id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (topic_id,))
            row = cur.fetchone()
            return dict(row) if row else None
def get_children(topic_id) -> list[dict[str, Any]]:
    query = """
        SELECT
            id,
            parent_id,
            name,
            node_type,
            sequence_order,
            description
        FROM roadmap_topics
        WHERE parent_id = %s
        ORDER BY sequence_order, id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (topic_id,))
            return [dict(row) for row in cur.fetchall()]
def get_next_topic(user_id) -> dict[str,Any] | None:

    query = """
                SELECT
            rt.id,
            rt.parent_id,
            rt.name,
            rt.node_type,
            rt.sequence_order,
            rt.description
        FROM roadmap_topics rt

        LEFT JOIN user_progress up
            ON up.roadmap_topic_id = rt.id
            AND up.user_id = %s

        WHERE
            rt.node_type = 'topic'
            AND (up.roadmap_topic_id IS NULL
                OR up.problems_solved = 0)
        ORDER BY
            rt.sequence_order,
            rt.id
        LIMIT 1;

    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id,))
            row = cur.fetchone()

            return dict(row) if row else None
def get_first_topic() -> dict[str, Any] | None:
    query = """
        SELECT
            id,
            parent_id,
            name,
            node_type,
            sequence_order,
            description
        FROM roadmap_topics
        WHERE node_type = 'topic'
        ORDER BY sequence_order ASC, id ASC
        LIMIT 1;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()

            return dict(row) if row else None
def debug_roadmap():
    query = """
        SELECT
            id,
            parent_id,
            name,
            node_type,
            sequence_order
        FROM roadmap_topics
        ORDER BY id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)

            rows = cur.fetchall()

            for row in rows:
                print(dict(row))
from .codefroce import fetch_codeforces_problems
from .repo import (
    save_problem,
    save_problem_topics,
    count_available_problems
)
from .normalizer import (
    normalize_topic,
    map_provider_tag,
    map_problem_topics,
    TAG_ALIASES
)


from scripts.setup import get_connection


def get_roadmap_topic_map() -> dict[str, int]:
    query = """
        SELECT id, name
        FROM roadmap_topics
        WHERE node_type IN ('topic', 'pattern', 'subpattern');
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)

            rows = cur.fetchall()

    return {
        normalize_topic(row["name"]): row["id"] # type: ignore
        for row in rows
    }
def ingest_codeforces(topic_id: int,
    difficulty: str,limit: int = 10) -> int:
    print(
        f"[INGEST] Fetching Codeforces problems "
        f"topic_id={topic_id}, "
        f"difficulty={difficulty}, "
        f"limit={limit}"
    )

    problems = fetch_codeforces_problems(limit=limit)
    roadmap_topics = get_roadmap_topic_map()

    inserted = 0

    for problem in problems:
        if problem.difficulty != difficulty:
            continue
        
        topic_ids = map_problem_topics(problem.topics, roadmap_topics)
        if not topic_ids:
            continue
        problem_id = save_problem(problem)
        save_problem_topics(problem_id, topic_ids)

        inserted += 1
        print(
            f"[INGEST] {problem.problem_id} | "
            f"{problem.title} | "
            f"{problem.difficulty}"
        )
        if inserted >= limit:
            break
        print(f"[INGEST] Added {inserted} problems")


    return inserted

def ensure_problem_pool(
    topic_id: int,
    difficulty: str,
    minimum: int = 5,
    refill: int = 10,
) -> int:
    current = count_available_problems(
        topic_id=topic_id,
        difficulty=difficulty,
    )
    print(
        f"[POOL] topic={topic_id} "
        f"difficulty={difficulty} "
        f"current={current} "
        f"minimum={minimum}"
    )
    if current >= minimum:
        print("[POOL] Enough problems available")
        return current
    needed = max(
        refill,
        minimum - current,
    )
    print(
        f"[POOL] Need more problems: {needed}"
    )
    added = ingest_codeforces(
        topic_id=topic_id,
        difficulty=difficulty,
        limit=needed,
    )
    final_count = count_available_problems(
        topic_id=topic_id,
        difficulty=difficulty,
    )
    print(
        f"[POOL] Final problem count: "
        f"{final_count}"
    )
    if final_count == 0:
        raise ValueError(
            "Unable to find Codeforces problems "
            f"for topic_id={topic_id}, "
            f"difficulty={difficulty}"
        )
    return final_count

if __name__ == "__main__":

    # Manual test only.

    # Example:
    # python -m Tools.ingestion.ingest

    topic_map = get_roadmap_topic_map()

    print("Available roadmap topics:")

    for name, topic_id in topic_map.items():

        print(
            f"{topic_id}: {name}"
        )
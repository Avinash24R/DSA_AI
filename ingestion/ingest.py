from .codefroce import fetch_codeforces_problems
from .leetcode import fetch_leetcode_problems
from .repo import (
    save_problem,
    save_problem_topics,
    count_available_problems
)
from .normalizer import (
    normalize_topic,
    map_provider_tag,
    build_roadmap_topic_map,
    map_problem_topics,
    expand_parent_topics,
    TAG_ALIASES,
    LEETCODE_TAG_ALIASES,
)


from scripts.setup import get_connection

def get_roadmap_topics() -> list[dict]:
    query = """
        SELECT
            id,
            parent_id,
            name,
            node_type
        FROM roadmap_topics
        WHERE node_type IN ('topic', 'pattern', 'subpattern')
        ORDER BY id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return [dict(row) for row in cur.fetchall()]

def get_roadmap_topic_map() -> dict[str, int]:
    rows = get_roadmap_topics()
    return {
        normalize_topic(row["name"]): row["id"]
        for row in rows
    }
def _ingest_provider(
    provider_name: str,
    fetch_fn,
    alias_map: dict[str, str],
    topic_id: int,
    difficulty: str,
    limit: int = 10,
) -> int:
    print(
        f"[INGEST] Fetching {provider_name} problems "
        f"topic_id={topic_id}, "
        f"difficulty={difficulty}, "
        f"limit={limit}"
    )

    problems = fetch_fn()

    print(f"[DEBUG] Total {provider_name} problems fetched: {len(problems)}")
    roadmap_rows = get_roadmap_topics()
    roadmap_topics = build_roadmap_topic_map(roadmap_rows)

    inserted = 0
    difficulty_matches = 0
    mapped_matches = 0
    requested_topic_matches = 0
    for problem in problems:

        if problem.difficulty != difficulty:
            continue
        difficulty_matches += 1

        mapped_topic_ids = map_problem_topics(
            problem.topics,
            roadmap_topics,
            alias_map=alias_map,
        )

        if not mapped_topic_ids:
            continue

        mapped_matches += 1

        topic_ids = expand_parent_topics(
            mapped_topic_ids,
            roadmap_rows
        )


        if topic_id not in topic_ids:
            continue
        requested_topic_matches += 1
        print(
            "[MATCH]",
            problem.problem_id,
            "|",
            problem.title,
            "|",
            provider_name,
            "tags=",
            problem.topics,
            "| roadmap IDs=",
            topic_ids
        )
        problem_id = save_problem(problem)
        save_problem_topics(problem_id, topic_ids)

        inserted += 1
        print(
            f"[INGEST] Added "
            f"{problem.problem_id} | "
            f"{problem.title} | "
            f"{problem.difficulty} | "
            f"topics={topic_ids}"
        )
        if inserted >= limit:
            break
    print(
        f"[DEBUG] {provider_name} difficulty matches = {difficulty_matches}"
    )

    print(
        f"[DEBUG] {provider_name} mapped topic matches = {mapped_matches}"
    )

    print(
        f"[DEBUG] {provider_name} requested topic matches = {requested_topic_matches}"
    )

    print(
        f"[DEBUG] {provider_name} inserted = {inserted}"
    )
    return inserted


def ingest_codeforces(topic_id: int,
    difficulty: str,limit: int = 10) -> int:
    return _ingest_provider(
        provider_name="codeforces",
        fetch_fn=fetch_codeforces_problems,
        alias_map=TAG_ALIASES,
        topic_id=topic_id,
        difficulty=difficulty,
        limit=limit,
    )


def ingest_leetcode(topic_id: int,
    difficulty: str, limit: int = 10) -> int:
    return _ingest_provider(
        provider_name="leetcode",
        fetch_fn=fetch_leetcode_problems,
        alias_map={**TAG_ALIASES, **LEETCODE_TAG_ALIASES},
        topic_id=topic_id,
        difficulty=difficulty,
        limit=limit,
    )

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

    print("[POOL] Trying Codeforces first...")
    try:
        ingest_codeforces(
            topic_id=topic_id,
            difficulty=difficulty,
            limit=needed,
        )
    except Exception as e:
        print(f"[POOL] Codeforces ingestion failed: {e}")

    current = count_available_problems(
        topic_id=topic_id,
        difficulty=difficulty,
    )

    if current < minimum:
        still_needed = max(refill, minimum - current)
        print(
            f"[POOL] Codeforces alone wasn't enough "
            f"({current}/{minimum}). Falling back to LeetCode "
            f"for {still_needed} more..."
        )
        try:
            ingest_leetcode(
                topic_id=topic_id,
                difficulty=difficulty,
                limit=still_needed,
            )
        except Exception as e:
            print(f"[POOL] LeetCode ingestion failed: {e}")

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
            "Unable to find Codeforces or LeetCode problems "
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
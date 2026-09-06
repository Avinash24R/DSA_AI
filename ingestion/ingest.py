from .codefroce import fetch_codeforces_problems
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
    TAG_ALIASES
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
def ingest_codeforces(topic_id: int,
    difficulty: str,limit: int = 10) -> int:
    print(
        f"[INGEST] Fetching Codeforces problems "
        f"topic_id={topic_id}, "
        f"difficulty={difficulty}, "
        f"limit={limit}"
    )

    problems = fetch_codeforces_problems()

    print(f"[DEBUG] Total CF problems fetched: {len(problems)}") 
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
            roadmap_topics
        )

        if not mapped_topic_ids:
            continue

        mapped_matches += 1

        topic_ids = expand_parent_topics(
            mapped_topic_ids,
            roadmap_rows
        )


        if topic_id not in topic_ids:
            print(
                "[NO MATCH]",
                problem.problem_id,
                "|",
                problem.title,
                "| CF tags=",
                problem.topics,
                "| mapped=",
                mapped_topic_ids,
                "| expanded=",
                topic_ids,
                "| requested=",
                topic_id,
            )
            continue
        requested_topic_matches += 1
        print(
            "[MATCH]",
            problem.problem_id,
            "|",
            problem.title,
            "| rating=",
            problem.metadata.get("rating"),
            "| CF tags=",
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
        print(f"[INGEST] Added {inserted} problems")
    print(
    f"[DEBUG] difficulty matches = {difficulty_matches}"
)

    print(
        f"[DEBUG] mapped topic matches = {mapped_matches}"
    )

    print(
        f"[DEBUG] requested topic matches = {requested_topic_matches}"
    )

    print(
        f"[DEBUG] inserted = {inserted}"
    )
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
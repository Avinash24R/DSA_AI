from .codefroce import fetch_codeforces_problems
from .repo import (
    save_problem,
    save_problem_topics,
)
from .normalizer import (
    normalize_topic,
    map_provider_tag
)


from scripts.setup import get_connection

TAG_ALIASES = {

    # Arrays
    "array": "Arrays",

    # Two pointer
    "two_pointers": "Two Pointer",
    "two_pointer": "Two Pointer",

    # Sliding window
    "sliding_window": "Sliding Window",

    # Binary search
    "binary_search": "Binary Search",

    # Prefix sum
    "prefix_sums": "Prefix Sum",
    "prefix_sum": "Prefix Sum",

    # Hashing
    "hash": "Hashing",
    "hashing": "Hashing",
    "hash_table": "Hashing",
    "data_structures": "Hashing",

    # Stack
    "stacks": "Stack",
    "stack": "Stack",

    # Queue
    "queues": "Queue",
    "queue": "Queue",

    # Graph
    "graphs": "Graph",
    "graph": "Graph",

    # Trees
    "trees": "Tree",
    "tree": "Tree",

    # DP
    "dp": "Dynamic Programming",
    "dynamic_programming": "Dynamic Programming",

    # Greedy
    "greedy": "Greedy",

    # Recursion
    "recursion": "Recursion",

    "backtracking": "Backtracking",
}

def map_problem_topics(
    provider_topics: list[str],
    roadmap_topics: dict[str, int],
) -> list[int]:

    topic_ids = []

    for tag in provider_topics:

        roadmap_name = TAG_ALIASES.get(tag)

        if not roadmap_name:
            continue

        topic_id = roadmap_topics.get(
            roadmap_name.lower()
        )

        if topic_id:
            topic_ids.append(topic_id)

    return list(set(topic_ids))
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
        row["name"].lower(): row["id"] # type: ignore
        for row in rows
    }
def ingest_codeforces(limit: int = 5) -> int:
    print(f"Fetching {limit} Codeforces problems...")

    problems = fetch_codeforces_problems(limit=limit)
    roadmap_topics = get_roadmap_topic_map()

    inserted = 0

    for problem in problems:
        problem_id = save_problem(problem)
        topic_ids = map_problem_topics(problem.topics, roadmap_topics)
        save_problem_topics(problem_id, topic_ids)

        inserted += 1
        print(f"Inserted: {problem.problem_id} | {problem.title}")

    return inserted


if __name__ == "__main__":
    ingest_codeforces(5)
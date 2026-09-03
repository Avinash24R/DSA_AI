import re
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

def normalize_topic(value: str) -> str:
    value = value.strip().lower()

    value = re.sub(r"[^a-z0-9]+", "_", value)

    value = re.sub(r"_+", "_", value)

    return value.strip("_")


def map_provider_tag(
    provider_tag: str,
    roadmap_topics: dict[str, int],
) -> int | None:

    normalized = normalize_topic(provider_tag)

    # 1. Direct match
    if normalized in roadmap_topics:
        return roadmap_topics[normalized]

    # 2. Alias
    alias = TAG_ALIASES.get(normalized)

    if alias is None:
        return None

    alias_normalized = normalize_topic(alias)
    return roadmap_topics.get(alias_normalized)
def map_problem_topics(
    provider_topics: list[str],
    roadmap_topics: dict[str, int],
) -> list[int]:

    topic_ids: set[int] = set()

    for provider_topic in provider_topics:

        topic_id = map_provider_tag(
            provider_topic,
            roadmap_topics,
        )

        if topic_id is not None:
            topic_ids.add(topic_id)

    return list(topic_ids)
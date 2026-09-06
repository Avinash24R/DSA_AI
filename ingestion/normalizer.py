import re
from scripts.setup import get_connection

TAG_ALIASES = {
    # Arrays
    "array": "Arrays",
    "arrays": "Arrays",

    "prefix_sum": "Prefix Sum",
    "prefix_sums": "Prefix Sum",
    "difference_array": "Difference Array",
    "difference_arrays": "Difference Array",
    "two_pointer": "Two Pointer",
    "two_pointers": "Two Pointer",
    "sliding_window": "Sliding Window",
    "binary_search": "Binary Search",

    # Hashing
    "hashing": "Hashing",
    "hash_table": "Hashing",

    # Stack
    "stack": "Monotonic Stack",
    "stacks": "Monotonic Stack",

    # Linked List
    "linked_list": "Linked List",
    "linked_lists": "Linked List",

    # Tree
    "trees": "Tree",
    "tree": "Tree",

    # Graph
    "graph": "Graph",
    "graphs": "Graph",
    "dfs_and_similar": "Graph",
    "dsu": "Graph",

    # DP
    "dp": "Dynamic Programming",
    "dynamic_programming": "Dynamic Programming",

    # Greedy
    "greedy": "Greedy",


    "backtracking": "Backtracking",

    "bitmasks": "Bit Manipulation",
    "bitmask": "Bit Manipulation",

    "math": "Math",
    "number_theory": "Math",
    "combinatorics": "Math",

    "data_structures": "Heap / Priority Queue",
}

def normalize_topic(value: str) -> str:
    value = value.strip().lower()

    value = re.sub(r"[^a-z0-9]+", "_", value)

    value = re.sub(r"_+", "_", value)

    return value.strip("_")

def build_roadmap_topic_map(roadmap_rows: list[dict])-> dict[str, int]:
    result = {}

    for row in roadmap_rows:
        key = normalize_topic(row["name"])

        result[key] = row["id"]

    return result
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
            roadmap_topics
        )

        if topic_id is not None:
            topic_ids.add(topic_id)

    return list(topic_ids)
def expand_parent_topics(
    topic_ids: list[int],
    roadmap_rows: list[dict],
) -> list[int]:
    parent_map = {
        row["id"]: row["parent_id"]
        for row in roadmap_rows
    }
    expanded = set(topic_ids)
    for topic_id in topic_ids:
        current = topic_id

        while current in parent_map:
            parent_id = parent_map[current]

            if parent_id is None:
                break

            expanded.add(parent_id)
            current = parent_id

    return list(expanded)
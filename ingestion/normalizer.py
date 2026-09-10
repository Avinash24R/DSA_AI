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
    "expression_parsing": "Expression Evaluation",

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
    "graph_matchings": "Graph",
    "shortest_paths": "Graph",
    "flows": "Graph",

    # DP
    "dp": "Dynamic Programming",
    "dynamic_programming": "Dynamic Programming",

    # Greedy
    "greedy": "Greedy",
    "sortings": "Greedy",
    "sorting": "Greedy",
    "schedules": "Greedy",

    "backtracking": "Backtracking",

    "bitmasks": "Bit Manipulation",
    "bitmask": "Bit Manipulation",

    "math": "Math",
    "number_theory": "Math",
    "combinatorics": "Math",
    "chinese_remainder_theorem": "Math",
    "probabilities": "Math",

    "strings": "String",
    "string": "String",
    "string_suffix_structures": "String",

    "ternary_search": "Binary Search",

    # Note: intentionally NOT mapped — these Codeforces tags are
    # too generic (they'd match almost every problem regardless of
    # topic) or have no equivalent roadmap topic, so leaving them
    # unmapped is more correct than forcing a guess:
    #   implementation, brute_force, data_structures, geometry,
    #   constructive_algorithms, interactive, games, matrices,
    #   divide_and_conquer, fft, meet_in_the_middle, 2_sat
}

# LeetCode's topic-tag vocabulary differs from Codeforces'; these
# are extra aliases layered on top of TAG_ALIASES for LeetCode-only
# tag spellings that don't already have an entry above.
LEETCODE_TAG_ALIASES = {
    "linked_list": "Linked List",
    "two_pointers": "Two Pointer",
    "sliding_window": "Sliding Window",
    "binary_search": "Binary Search",
    "stack": "Monotonic Stack",
    "monotonic_stack": "Monotonic Stack",
    "queue": "Queue",
    "monotonic_queue": "Monotonic Queue",
    "hash_table": "Hashing",
    "breadth_first_search": "BFS",
    "depth_first_search": "DFS",
    "binary_tree": "Binary Tree",
    "binary_search_tree": "Binary Search Tree",
    "tree": "Tree",
    "graph": "Graph",
    "topological_sort": "Topological Sort",
    "union_find": "DSU",
    "minimum_spanning_tree": "MST",
    "shortest_path": "Shortest Path",
    "heap_priority_queue": "Heap / Priority Queue",
    "greedy": "Greedy",
    "dynamic_programming": "Dynamic Programming",
    "backtracking": "Backtracking",
    "bit_manipulation": "Bit Manipulation",
    "bitmask": "Bitmask",
    "math": "Math",
    "number_theory": "Number Theory",
    "combinatorics": "Combinatorics",
    "sorting": "Greedy",
    "string": "String",
    "recursion": "Backtracking",
    "prefix_sum": "Prefix Sum",
    "subsets": "Subsets",
    "counting": "Frequency Map",
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
    alias_map: dict[str, str] | None = None,
) -> int | None:

    normalized = normalize_topic(provider_tag)

    # 1. Direct match
    if normalized in roadmap_topics:
        return roadmap_topics[normalized]

    # 2. Alias
    aliases = alias_map if alias_map is not None else TAG_ALIASES
    alias = aliases.get(normalized)

    if alias is None:
        return None

    alias_normalized = normalize_topic(alias)
    return roadmap_topics.get(alias_normalized)
def map_problem_topics(
    provider_topics: list[str],
    roadmap_topics: dict[str, int],
    alias_map: dict[str, str] | None = None,
) -> list[int]:
    topic_ids: set[int] = set()
    for provider_topic in provider_topics:
        topic_id = map_provider_tag(
            provider_topic,
            roadmap_topics,
            alias_map=alias_map,
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
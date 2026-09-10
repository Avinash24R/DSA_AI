"""
Seed LeetCode problems into the shared `problems` table for every
roadmap topic and difficulty.

Usage:
    python -m scripts.seed_leetcode
    python -m scripts.seed_leetcode --minimum 8 --refill 15
    python -m scripts.seed_leetcode --topic-id 3

This only touches LeetCode — run `scripts/seed_codeforces.py` (or let
`ensure_problem_pool` pull Codeforces on demand) for that source.
Codeforces has good tag coverage for algorithmic-technique topics
(Graph, DP, Greedy, Math, ...) but no real tags for plain
data-structure topics (Arrays, Linked List, Stack, Queue, ...), so
those topics will rely on LeetCode almost entirely — this script is
what fills that gap.
"""

import argparse

from ingestion.ingest import ingest_leetcode, get_roadmap_topics
from ingestion.repo import count_available_problems

DIFFICULTIES = ["easy", "medium", "hard"]


def seed_leetcode(minimum: int = 5, refill: int = 15, topic_id: int | None = None):
    topics = [
        t for t in get_roadmap_topics()
        if t["node_type"] == "topic" and (topic_id is None or t["id"] == topic_id)
    ]

    if not topics:
        print("No matching roadmap topics found.")
        return

    report: list[tuple[str, str, int]] = []

    for topic in topics:
        for difficulty in DIFFICULTIES:
            current = count_available_problems(
                topic_id=topic["id"], difficulty=difficulty
            )

            if current < minimum:
                print(
                    f"\n=== {topic['name']} / {difficulty} "
                    f"(have {current}, need {minimum}) ==="
                )
                try:
                    ingest_leetcode(
                        topic_id=topic["id"],
                        difficulty=difficulty,
                        limit=max(refill, minimum - current),
                    )
                except Exception as e:
                    print(f"[SEED] Failed for {topic['name']}/{difficulty}: {e}")

            final = count_available_problems(
                topic_id=topic["id"], difficulty=difficulty
            )
            report.append((topic["name"], difficulty, final))

    print("\n" + "=" * 60)
    print("COVERAGE REPORT (problems available per topic/difficulty)")
    print("=" * 60)

    weak_spots = []
    for name, difficulty, count in report:
        flag = "  <-- LOW" if count < minimum else ""
        print(f"{name:30s} {difficulty:8s} {count:4d}{flag}")
        if count < minimum:
            weak_spots.append((name, difficulty, count))

    print("=" * 60)
    if weak_spots:
        print(f"{len(weak_spots)} topic/difficulty combos are still below the minimum:")
        for name, difficulty, count in weak_spots:
            print(f"  - {name} ({difficulty}): only {count} problems")
        print(
            "These roadmap topics likely don't have a matching LeetCode "
            "or Codeforces tag — check ingestion/normalizer.py's tag "
            "alias maps."
        )
    else:
        print("Every topic/difficulty has at least the minimum problem count.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minimum", type=int, default=5, help="Minimum problems required per topic/difficulty")
    parser.add_argument("--refill", type=int, default=15, help="How many to fetch per pass when below minimum")
    parser.add_argument("--topic-id", type=int, default=None, help="Only seed this roadmap topic id")
    args = parser.parse_args()

    seed_leetcode(minimum=args.minimum, refill=args.refill, topic_id=args.topic_id)

"""
Seed Codeforces problems into the shared `problems` table for every
roadmap topic and difficulty.

Usage:
    python -m scripts.seed_codeforces
    python -m scripts.seed_codeforces --minimum 8 --refill 15
    python -m scripts.seed_codeforces --topic-id 3

Note: Codeforces' tag vocabulary (math, greedy, graphs, dp, strings,
two pointers, ...) covers algorithmic techniques well but has no real
tags for plain data-structure topics (Arrays, Linked List, Stack,
Queue, ...). Those topics will stay short here no matter how the
alias map is tuned — run `scripts/seed_leetcode.py` afterwards (or
just rely on `ensure_problem_pool`'s automatic fallback) to fill
those in from LeetCode instead.
"""

import argparse

from ingestion.ingest import ingest_codeforces, get_roadmap_topics
from ingestion.repo import count_available_problems

DIFFICULTIES = ["easy", "medium", "hard"]


def seed_codeforces(minimum: int = 5, refill: int = 15, topic_id: int | None = None):
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
                    ingest_codeforces(
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
        flag = "  <-- LOW (try scripts/seed_leetcode.py)" if count < minimum else ""
        print(f"{name:30s} {difficulty:8s} {count:4d}{flag}")
        if count < minimum:
            weak_spots.append((name, difficulty, count))

    print("=" * 60)
    if weak_spots:
        print(f"{len(weak_spots)} topic/difficulty combos are still below the minimum.")
        print("This is expected for pure data-structure topics — Codeforces")
        print("doesn't tag them. Run scripts/seed_leetcode.py to fill the gap.")
    else:
        print("Every topic/difficulty has at least the minimum problem count.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minimum", type=int, default=5, help="Minimum problems required per topic/difficulty")
    parser.add_argument("--refill", type=int, default=15, help="How many to fetch per pass when below minimum")
    parser.add_argument("--topic-id", type=int, default=None, help="Only seed this roadmap topic id")
    args = parser.parse_args()

    seed_codeforces(minimum=args.minimum, refill=args.refill, topic_id=args.topic_id)

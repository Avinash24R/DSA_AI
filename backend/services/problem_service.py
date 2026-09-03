from ingestion.ingest import ensure_problem_pool
def prepare_problem_pool(
    topic_id: int,
    topic_name: str,
    difficulty: str,
) -> int:

    difficulty = (
        difficulty
        or "easy"
    ).strip().lower()

    print(
        "[PROBLEM SERVICE] "
        f"Preparing problems for "
        f"{topic_name} / {difficulty}"
    )

    count = ensure_problem_pool(
        topic_id=topic_id,
        difficulty=difficulty,
        minimum=5,
        refill=10,
    )

    print(
        "[PROBLEM SERVICE] "
        f"Ready with {count} problems"
    )

    return count
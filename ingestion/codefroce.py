import requests

from .models import Problem


BASE_URL = "https://codeforces.com/api/problemset.problems"


def normalize_difficulty(rating: int) -> str:
    if rating <= 1000:
        return "easy"
    if rating <= 1500:
        return "medium"
    return "hard"


def normalize_topic(tag: str) -> str:
    return (
        tag.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def fetch_codeforces_problems(
    limit: int | None = None,
) -> list[Problem]:

    response = requests.get(
        BASE_URL,
        params={"lang": "en"},
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data["status"] != "OK":
        raise RuntimeError(
            f"Codeforces API error: {data.get('comment')}"
        )

    problems = []

    for item in data["result"]["problems"]:

        if item.get("type") != "PROGRAMMING":
            continue

        contest_id = item.get("contestId")
        index = item.get("index")
        rating = item.get("rating")

        if contest_id is None or index is None:
            continue

        if rating is None:
            continue

        problem = Problem(
            source="codeforces",
            problem_id=f"codeforces:{contest_id}:{index}",
            title=item["name"],
            difficulty=normalize_difficulty(rating),
            topics=[
                normalize_topic(tag)
                for tag in item.get("tags", [])
            ],
            url=(
                f"https://codeforces.com/problemset/problem/"
                f"{contest_id}/{index}"
            ),
            metadata={
                "contest_id": contest_id,
                "index": index,
                "rating": rating,
                "type": item.get("type"),
            },
        )

        problems.append(problem)

        if limit and len(problems) >= limit:
            break

    return problems
import requests
from .models import Problem

GRAPHQL_URL = "https://leetcode.com/graphql"

PROBLEMSET_QUERY = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
  problemsetQuestionList: questionList(
    categorySlug: $categorySlug
    limit: $limit
    skip: $skip
    filters: $filters
  ) {
    total: totalNum
    questions: data {
      questionFrontendId
      title
      titleSlug
      difficulty
      isPaidOnly
      acRate
      topicTags {
        name
        slug
      }
    }
  }
}
"""

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com/problemset/all/",
    "User-Agent": "Mozilla/5.0 (DSA-AI-Tutor ingestion bot)",
}


def normalize_difficulty(difficulty: str) -> str:
    return (difficulty or "").strip().lower()


def normalize_topic(tag: str) -> str:
    return (
        tag.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def fetch_leetcode_problems(
    include_paid_only: bool = False,
    page_size: int = 100,
    max_pages: int = 50,
) -> list[Problem]:
    """
    Pull the full LeetCode "algorithms" problem list (with topic
    tags) via LeetCode's public GraphQL endpoint, paginating until
    every problem has been fetched.

    By default premium-only ("Premium/free status") problems are
    skipped since they can't actually be solved/verified without a
    LeetCode subscription.
    """

    problems: list[Problem] = []
    skip = 0

    for _ in range(max_pages):
        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": PROBLEMSET_QUERY,
                "variables": {
                    "categorySlug": "algorithms",
                    "skip": skip,
                    "limit": page_size,
                    "filters": {},
                },
            },
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        payload = response.json()
        data = payload.get("data", {}).get("problemsetQuestionList")

        if not data:
            raise RuntimeError(f"LeetCode API error: {payload}")

        questions = data.get("questions", [])

        if not questions:
            break

        for item in questions:
            is_paid_only = bool(item.get("isPaidOnly"))

            if is_paid_only and not include_paid_only:
                continue

            slug = item.get("titleSlug")
            frontend_id = item.get("questionFrontendId")
            difficulty = item.get("difficulty")

            if not slug or not frontend_id or not difficulty:
                continue

            problem = Problem(
                source="leetcode",
                problem_id=f"leetcode:{slug}",
                title=item.get("title", slug),
                difficulty=normalize_difficulty(difficulty),
                topics=[
                    normalize_topic(tag["slug"])
                    for tag in item.get("topicTags", [])
                    if tag.get("slug")
                ],
                url=f"https://leetcode.com/problems/{slug}/",
                metadata={
                    "frontend_id": frontend_id,
                    "slug": slug,
                    "is_paid_only": is_paid_only,
                    "acceptance_rate": item.get("acRate"),
                },
            )

            problems.append(problem)

        skip += page_size

        if skip >= data.get("total", 0):
            break

    return problems

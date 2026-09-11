import requests
from datetime import datetime, timezone

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

# recentAcSubmissionList is the same public endpoint LeetCode's own
# profile page uses to show "Recent AC" — it only returns Accepted
# submissions and works for any username without authentication
# (unless the user has made their submissions private).
RECENT_AC_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
    lang
  }
}
"""

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0 (DSA-AI-Tutor submission checker)",
}


def get_recent_accepted_submissions(handle: str, limit: int = 20) -> list[dict]:
    response = requests.post(
        LEETCODE_GRAPHQL,
        json={
            "query": RECENT_AC_QUERY,
            "variables": {"username": handle, "limit": limit},
        },
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()

    payload = response.json()

    if payload.get("errors"):
        raise ValueError(
            payload["errors"][0].get("message", "LeetCode API error")
        )

    data = payload.get("data", {}).get("recentAcSubmissionList")

    if data is None:
        raise ValueError(
            "LeetCode returned no data — check the username is correct "
            "and that submissions aren't set to private."
        )

    return data


def check_leetcode_submission(handle: str, slug: str, assigned_at) -> dict:
    """
    Mirrors check_codeforces_submission()'s shape/behaviour: looks at
    the student's most recent Accepted submissions and only counts one
    as belonging to this assignment if it's for the right problem and
    happened after the problem was assigned.

    LeetCode's public API only exposes Accepted submissions (no
    "recent submissions" list with verdicts for wrong answers is
    publicly readable), so an unmatched result just means "not solved
    yet" rather than "found but rejected".
    """
    submissions = get_recent_accepted_submissions(handle=handle, limit=20)

    for sub in submissions:
        if sub.get("titleSlug") != slug:
            continue

        timestamp = sub.get("timestamp")
        try:
            submission_time = datetime.fromtimestamp(int(timestamp), tz=timezone.utc) # type: ignore
        except (TypeError, ValueError):
            continue

        if submission_time <= assigned_at:
            continue

        return {
            "source": "leetcode",
            "found": True,
            "accepted": True,
            "verdict": "Accepted",
            "submission_id": sub.get("id"),
            "language": sub.get("lang"),
            "creation_time": timestamp,
            "slug": slug,
        }

    return {
        "source": "leetcode",
        "found": False,
        "accepted": False,
        "verdict": None,
        "submission_id": None,
        "language": None,
        "creation_time": None,
        "slug": slug,
    }
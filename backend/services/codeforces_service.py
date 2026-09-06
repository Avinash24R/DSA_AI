import requests
from scripts.setup import get_connection
from datetime import datetime, timezone

CODEFORCES_API = "https://codeforces.com/api"

def get_user_submissions(handle: str , count : int = 100)-> list[dict]:
    res = requests.get(f"{CODEFORCES_API}/user.status", 
        params={
        "handle": handle,
        "count": count,
        },
        timeout=15,
    )
    res.raise_for_status()
    data = res.json()

    if data.get("status") != "ok":
        raise ValueError(data.get("comment","Codeforces API error"))
    return data["result"]
def check_codeforces_submission(handle: str , contest_id : int, problem_index : str , assigned_at) -> dict:
    submission = get_user_submissions(handle=handle, count= 100)
    for sub in submission:
        problem = sub.get("problem", {})
        if (problem.get("contestId") != contest_id or problem.get("index") != problem_index):
            continue
        created_time_seconds =sub.get("creationTimeSeconds")
        submission_time = datetime.fromtimestamp(created_time_seconds, tz=timezone.utc) # type: ignore
        if submission_time <= assigned_at:
            continue
        return {
            "source": "codeforces",
            "found": True,
            "accepted":
                sub.get("verdict") == "OK",
            "verdict":sub.get("verdict"),
            "submission_id": sub.get("id"),
            "language": sub.get("programmingLanguage"),
            "creation_time":
                sub.get(
                    "creationTimeSeconds"
                ),
            "contest_id":
                contest_id,
            "problem_index":
                problem_index,
        }


    return {
        "source": "codeforces",
        "found": False,
        "accepted": False,
        "verdict": None,
        "submission_id": None,
        "language": None,
        "creation_time": None,
        "contest_id": contest_id,
        "problem_index": problem_index,
    }

def get_problem_assignment(
    assignment_id: int,
) -> dict | None:

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    user_id,
                    problem_id,
                    assigned_at,
                    submitted_at,
                    codeforces_submission_id,
                    status
                FROM problem_assignments
                WHERE id = %s
                """,
                (assignment_id,),
            )

            row = cur.fetchone()

    if not row:
        return None

    if isinstance(row, dict):
        return row

    return {
        "id": row[0],
        "user_id": row[1],
        "problem_id": row[2],
        "assigned_at": row[3],
        "submitted_at": row[4],
        "codeforces_submission_id": row[5],
        "status": row[6],
    }
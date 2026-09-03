import requests

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
def check_codeforces_submission(handle: str , contest_id : int, problem_index : str) -> dict:
    submission = get_user_submissions(handle=handle, count= 100)
    for sub in submission:
        problem = sub.get("problem", {})
        if (problem.get("contestId")==contest_id and problem.get("index") == problem_index):
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
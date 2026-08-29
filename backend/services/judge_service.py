import os 
import httpx

JUDGE0_URL = os.getenv(
    "JUDGE0_URL",
    "http://localhost:2358"
)

LANGUAGE_IDS = {
    "cpp": 54,
    "c++": 54,
    "c": 50,
    "python": 71,
    "java": 62,
}
#judge0's submmission api accepts source_code , language , std_in and expected_output 
async def run_code(code: str,language: str,test_cases: list[dict],) -> dict:
    language_id = LANGUAGE_IDS.get(language.lower())

    if not language_id:
        raise ValueError(
            f"Unsupported language : {language}"
        )
    results = [] 
    async with httpx.AsyncClient(timeout=30) as client:
        for test_case in test_cases:
            payload = {
                "language_id": language_id,
                "source_code": code,
                "stdin": test_case["input"],
                "expected_output": test_case["expected_output"],
                "cpu_time_limit": 2,
                "memory_limit": 128000,
            }
            response = await client.post(
                f"{JUDGE0_URL}/submissions",
                params={
                    "base64_encoded": "false",
                    "wait": "true",
                },
                json=payload,
            )
            response.raise_for_status()

            result = response.json()

            results.append(result)

            # Stop immediately on failure
            if result.get("status", {}).get("id") != 3:
                break
    passed = sum(1 for res in results if res.get("status" , {}).get("id") == 3)
    total = len(test_cases)
    last_result = results[-1] if results else {}
    accepted = (
        passed == total and total > 0
    )
    return {
        "status": (
            "Accepted"
            if accepted
            else last_result.get(
                "status",
                {}
            ).get(
                "description",
                "Failed"
            )
        ),

        "accepted": accepted,

        "runtime_ms": (
            float(last_result["time"]) * 1000
            if last_result.get("time")
            else None
        ),

        "memory_kb": last_result.get("memory"),

        "stdout": last_result.get("stdout"),

        "stderr": last_result.get("stderr"),

        "compile_output": last_result.get(
            "compile_output"
        ),        
        "message": last_result.get(
            "message"
        ),

        "tests_passed": passed,

        "tests_total": total,
    }
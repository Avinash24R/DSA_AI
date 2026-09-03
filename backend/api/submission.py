from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import subprocess
import tempfile
import os
from scripts.setup import get_connection
from Agent.graph import graph
from langchain_core.runnables import RunnableConfig
from typing import Any, Mapping, cast
from langgraph.types import Command

router = APIRouter(prefix="/api", tags=["submission"])


class CodeSubmission(BaseModel):
    language: str
    code: str


def run_cpp_judge(code: str, test_cases: list[dict]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        source_file = tmp_path / "main.cpp"
        executable = tmp_path / "solution.exe"

        source_file.write_text(code, encoding="utf-8")

        compile_result = subprocess.run(
            [
                "g++",
                "-std=c++17",
                str(source_file),
                "-O2",
                "-o",
                str(executable),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if compile_result.returncode != 0:
            return {
                "status": "compilation_error",
                "accepted": False,
                "runtime_ms": 0,
                "memory_kb": 0,
                "tests_passed": 0,
                "tests_total": len(test_cases),
                "error": compile_result.stderr,
            }

        passed = 0

        for test in test_cases:
            try:
                result = subprocess.run(
                    [str(executable)],
                    input=test["input"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
            except subprocess.TimeoutExpired:
                return {
                    "status": "time_limit_exceeded",
                    "accepted": False,
                    "runtime_ms": 2000,
                    "memory_kb": 0,
                    "tests_passed": passed,
                    "tests_total": len(test_cases),
                }

            if result.returncode != 0:
                return {
                    "status": "runtime_error",
                    "accepted": False,
                    "runtime_ms": 0,
                    "memory_kb": 0,
                    "tests_passed": passed,
                    "tests_total": len(test_cases),
                    "error": result.stderr,
                }

            actual = result.stdout.strip()
            expected = test["output"].strip()

            if actual != expected:
                return {
                    "status": "wrong_answer",
                    "accepted": False,
                    "runtime_ms": 0,
                    "memory_kb": 0,
                    "tests_passed": passed,
                    "tests_total": len(test_cases),
                    "expected": expected,
                    "actual": actual,
                }

            passed += 1

        return {
            "status": "accepted",
            "accepted": True,
            "runtime_ms": 0,
            "memory_kb": 0,
            "tests_passed": passed,
            "tests_total": len(test_cases),
        }


def normalize_test_case_row(row: Mapping[str, Any] | tuple[Any, ...]) -> dict[str, str]:
    if isinstance(row, dict):
        row_dict = cast(dict[str, Any], row)
    elif hasattr(row, "keys"):
        row_dict = cast(dict[str, Any], dict(row))
    else:
        row_values = cast(tuple[Any, ...], row)
        row_dict = {
            "input": row_values[0],
            "output": row_values[1] if len(row_values) > 1 else "",
        }

    input_value = row_dict.get("input")
    output_value = row_dict.get("expected_output")
    if output_value is None:
        output_value = row_dict.get("output")

    if input_value is None or output_value is None:
        raise KeyError("Test case row missing input or output value")

    return {
        "input": str(input_value),
        "output": str(output_value),
    }
def get_test_cases(problem: dict) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT input, expected_output
                FROM problem_test_cases
                WHERE problem_id = %s
                ORDER BY id
                """,
                (problem["id"],),
            )

            rows = cur.fetchall()

    return [
        {
            "input": str(row["input"] if isinstance(row, dict) else row[0]), # type: ignore
            "output": str(
                row["expected_output"] # type: ignore
                if isinstance(row, dict)
                else row[1]
            ),
        }
        for row in rows
    ]
@router.post("/agent/session/{thread_id}/submit")
def submit_code(
    thread_id: str,
    submission: CodeSubmission,
):
    if submission.language.lower() != "cpp":
        raise HTTPException(
            status_code=400,
            detail="Currently only C++ is supported",
        )

    config = cast(RunnableConfig, {
        "configurable": {
            "thread_id": thread_id
        }
    })

    state = graph.get_state(config)

    if not state or not state.values:
        raise HTTPException(
            status_code=404,
            detail="Agent session not found",
        )

    current_state = state.values

    
    problem = current_state.get("current_problem")
    if not problem:
        raise HTTPException(
            status_code=400,
            detail="No active problem in session",
        )
    print("CURRENT PROBLEM:", problem)

    test_cases = get_test_cases(problem)
    if not test_cases:
        raise HTTPException(
            status_code=500,
            detail=f"No test cases found for problem_id={problem.get('id')}",
        )
    print("TEST CASES:", test_cases)
    judge_result = run_cpp_judge(
        submission.code,
        test_cases,
    )
    print("JUDGE RESULT:", judge_result)
    # Resume LangGraph
    result = graph.invoke(
        Command(
            resume={
                "user_answer": submission.code,
                "judge_result": judge_result,
            }
        ),
        config=config,
    )
    print("GRAPH RESULT:", result)

    return {
        "status": judge_result["status"],
        "judge_result": judge_result,
        "state": result,
        "next_action": result.get(
            "next_action",
            "EVALUATE",
        ),
    }
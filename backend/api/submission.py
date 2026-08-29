from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import subprocess
import tempfile
import os

from Agent.graph import build_graph
from langchain_core.runnables import RunnableConfig
from typing import cast
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


def get_test_cases(problem: dict) -> list[dict]:
    return [
        {
            "input": "5\n1 2 3 4 5\n",
            "output": "15",
        },
        {
            "input": "3\n10 20 30\n",
            "output": "60",
        },
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

    graph = build_graph()

    config = cast(RunnableConfig, {
        "configurable": {
            "thread_id": thread_id
        }
    })

    # Get the current LangGraph state
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

    test_cases = get_test_cases(problem)

    judge_result = run_cpp_judge(
        submission.code,
        test_cases,
    )

    # Resume LangGraph after interrupt()
    result = graph.invoke(
        Command(resume={
            "user_answer": submission.code,
            "judge_result": judge_result,
        }),
        config=config,
    )

    return {
        "status": judge_result["status"],
        "judge_result": judge_result,
        "next_action": result.get(
            "next_action",
            "EVALUATE",
        ),
    }
from typing import Any, cast
from langchain_core.runnables import RunnableConfig
from Agent.graph import build_graph
from Agent.state import DSAState
from scripts.setup import get_connection
from langgraph.types import Command
from Tools.roadmap_tools import get_roadmap


def require_row(cursor: Any) -> dict[str, Any]:
    row = cursor.fetchone()

    assert row is not None

    return cast(dict[str, Any], row)


def create_test_user() -> int:

    query = """
        INSERT INTO users (username)
        VALUES (%s)
        ON CONFLICT (username)
        DO UPDATE SET username = EXCLUDED.username
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                query,
                ("e2e_test_user",)
            )

            row = require_row(cur)

        conn.commit()

    return int(row["id"])


def get_latest_attempt(user_id: int) -> dict[str, Any] | None:

    query = """
        SELECT
            user_id,
            roadmap_topic_id,
            problem_id,
            correct,
            overall_score,
            evaluation
        FROM problem_attempts
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(query, (user_id,))

            row = cur.fetchone()

            if row is None:
                return None

            return cast(dict[str, Any], row)


def get_progress(
    user_id: int,
    topic_id: int,
) -> dict[str, Any] | None:

    query = """
        SELECT
            skill_score,
            weak_score,
            problems_attempted,
            problems_solved,
            avg_thinking_time_seconds
        FROM user_progress
        WHERE user_id = %s
          AND roadmap_topic_id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                query,
                (user_id, topic_id)
            )

            row = cur.fetchone()

            if row is None:
                return None

            return cast(dict[str, Any], row)


def test_complete_agent_session():

    user_id = create_test_user()

    roadmap = get_roadmap()

    print("\n========== ROADMAP ==========")

    for topic in roadmap:
        print(topic)

    topic_names = {
        row["name"]
        for row in roadmap
        if row["node_type"] == "topic"
    }

    assert "Arrays" in topic_names, (
        f"Arrays topic missing. Found topics: {topic_names}"
    )

    print("\nUSER ID:", user_id)

    graph = build_graph()

    config = cast(RunnableConfig, {
        "configurable": {
            "thread_id": f"e2e-test-{user_id}"
        }
    })

    # Explicitly type the state as DSAState.
    initial_state: DSAState = {
        "user_id": user_id,
    }


    result = graph.invoke(
        initial_state,
        config=config,
    )

    print("\n========== GRAPH PAUSED ==========")

    print("Topic:")
    print(result.get("current_topic"))

    print("\nProblem:")
    print(result.get("current_problem"))


    assert result.get("current_problem") is not None
    assert result.get("current_problem_id") is not None


    fake_answer = """
    #include <bits/stdc++.h>
    using namespace std;

    int main() {

        // Fake submission for E2E testing
        cout << "print(hello)"

        return 0;
    }
    """


    result = graph.invoke(
        Command(resume=fake_answer),
        config=config,
    )

    print("\n========== FINAL STATE ==========")

    print(result)


    assert result.get("next_action") == "END"

    assert result.get("current_topic_id") is not None
    assert result.get("current_problem_id") is not None
    assert result.get("current_problem") is not None
    assert result.get("evaluation") is not None


    attempt = get_latest_attempt(user_id)

    print("\n========== SAVED ATTEMPT ==========")

    print(attempt)

    assert attempt is not None

    assert attempt["user_id"] == user_id

    assert (
        attempt["problem_id"]
        == result["current_problem_id"]
    )


    topic_id = result["current_topic_id"]

    progress = get_progress(
        user_id,
        topic_id,
    )

    print("\n========== UPDATED PROGRESS ==========")

    print(progress)

    assert progress is not None

    assert progress["problems_attempted"] >= 1


    print("\n========== E2E TEST PASSED ==========")
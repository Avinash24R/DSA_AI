from typing import Any, cast

from backend.api.submission import normalize_test_case_row
from scripts.setup import get_connection

from ingestion.codefroce import (
    fetch_codeforces_problems,
)

from ingestion.ingest import (
    ingest_codeforces,
)


def require_row(cursor: Any) -> dict[str, Any]:
    row = cursor.fetchone()
    assert row is not None
    return cast(dict[str, Any], row)


def test_database_is_running():

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT 1 AS health;"
            )

            row = require_row(cur)

            assert row["health"] == 1


def test_roadmap_exists():

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM roadmap_topics;
            """)

            row = require_row(cur)

            assert row["count"] > 0


def test_roadmap_contains_arrays():

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT id
                FROM roadmap_topics
                WHERE name = 'Arrays';
            """)

            row = require_row(cur)

            assert row is not None


def test_codeforces_api():

    problems = fetch_codeforces_problems(
        limit=5
    )

    assert len(problems) == 5

    for problem in problems:

        assert problem.source == "codeforces"

        assert problem.problem_id.startswith(
            "codeforces:"
        )

        assert problem.title

        assert problem.difficulty in {
            "easy",
            "medium",
            "hard",
        }

        assert problem.url.startswith(
            "https://codeforces.com/"
        )


def test_codeforces_ingestion():

    inserted = ingest_codeforces(
        limit=5
    )

    assert inserted == 5


def test_problems_were_saved():

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM problems
                WHERE source = 'codeforces';
            """)

            row = require_row(cur)

            assert row["count"] >= 5


def test_problem_data_is_valid():

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    source,
                    external_id,
                    title,
                    difficulty,
                    url,
                    topics
                FROM problems
                WHERE source = 'codeforces'
                LIMIT 5;
            """)

            rows = cur.fetchall()

            assert len(rows) > 0

            for row in rows:
                assert isinstance(row, dict)
                row = cast(dict[str, Any], row)

                assert row["source"] == "codeforces"
                assert row["external_id"]
                assert row["title"]
                assert row["difficulty"]
                assert row["url"]
                assert row["topics"] is not None


def test_normalize_test_case_row_supports_output_alias():
    expected = normalize_test_case_row({"input": "2\n", "expected_output": "4\n"})
    actual = normalize_test_case_row({"input": "2\n", "output": "4\n"})

    assert expected == {"input": "2\n", "output": "4\n"}
    assert actual == {"input": "2\n", "output": "4\n"}


def test_problem_topic_mapping():

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM problem_topics pt
                JOIN problems p
                    ON p.id = pt.problem_id
                WHERE p.source = 'codeforces';
            """)

            row = require_row(cur)

            assert row["count"] > 0
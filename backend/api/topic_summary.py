from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scripts.setup import get_connection


router = APIRouter(
    prefix="/api/topic-summary",
    tags=["Topic Summary"],
)


class TopicSummaryCreate(BaseModel):
    user_id: int
    roadmap_topic_id: int | None = None
    topic_name: str
    summary: str


@router.post("")
def save_topic_summary(payload: TopicSummaryCreate):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO topic_summaries (
                        user_id,
                        roadmap_topic_id,
                        topic_name,
                        summary
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    ON CONFLICT (
                        user_id,
                        roadmap_topic_id
                    )
                    DO UPDATE SET
                        topic_name = EXCLUDED.topic_name,
                        summary = EXCLUDED.summary,
                        updated_at = NOW()
                    RETURNING
                        id,
                        user_id,
                        roadmap_topic_id,
                        topic_name,
                        summary,
                        created_at,
                        updated_at;
                    """,
                    (
                        payload.user_id,
                        payload.roadmap_topic_id,
                        payload.topic_name,
                        payload.summary,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return row
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
@router.get("")
def get_topic_summaries(user_id: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        user_id,
                        roadmap_topic_id,
                        topic_name,
                        summary,
                        created_at,
                        updated_at
                    FROM topic_summaries
                    WHERE user_id = %s
                    ORDER BY updated_at DESC;
                    """,
                    (user_id,),
                )

                rows = cur.fetchall()
        return {
            "summaries": rows
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
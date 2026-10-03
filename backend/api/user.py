
from typing import Any, cast

from fastapi import APIRouter, HTTPException
from backend.schemas.user import UserCreate, ApiKeyUpdate
from scripts.setup import get_connection


def _row_value(row: object | None, field_name: str, index: int = 0) -> Any | None:
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(field_name)
    if isinstance(row, (list, tuple)) and index < len(row):
        return row[index]
    return None


router = APIRouter(prefix="/api/users", tags=["user"])

@router.post("")
def create_user(user:UserCreate):
    query = """
    INSERT INTO users(name,email,level, codeforces_handle, leetcode_handle, groq_api_key)
    VALUES(%s,%s,%s,%s,%s,%s)
    ON CONFLICT(email)
    DO UPDATE SET
        name=EXCLUDED.name,
        level=EXCLUDED.level,
        codeforces_handle=EXCLUDED.codeforces_handle,
        leetcode_handle=EXCLUDED.leetcode_handle,
        -- Don't clobber an already-stored key with a blank one just
        -- because the onboarding form was resubmitted without it.
        groq_api_key=COALESCE(EXCLUDED.groq_api_key, users.groq_api_key)
    RETURNING id,name,email,level,codeforces_handle,leetcode_handle,(groq_api_key IS NOT NULL) AS has_api_key;
    """

    api_key = (user.groq_api_key or "").strip() or None

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user.name, user.email, user.level, user.codeforces_handle, user.leetcode_handle, api_key))
                row = cur.fetchone()
            conn.commit()

        if row is None:
            raise HTTPException(status_code=500, detail="User creation failed: no row returned")

        if isinstance(row, dict):
            user_row = cast(dict[str, Any], row)
        else:
            user_row = {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "level": row[3],
                "codeforces_handle": row[4],
                "leetcode_handle": row[5],
                "has_api_key": row[6],
            }

        return {
            "user_id": user_row["id"],
            "name": user_row["name"],
            "email": user_row["email"],
            "level": user_row["level"],
            "codeforces_handle": user_row["codeforces_handle"],
            "leetcode_handle": user_row["leetcode_handle"],
            # The key itself is never returned - only whether one is set,
            # so the frontend can show "key saved" vs. an empty field.
            "has_api_key": user_row["has_api_key"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/api-key")
def set_api_key(user_id: int, payload: ApiKeyUpdate):
    """
    Set or clear the student's personal Groq API key. Clearing it
    (null or "") makes the app fall back to the shared GROQ_API key
    from the backend's .env for this student again.
    """
    api_key = (payload.groq_api_key or "").strip() or None

    query = """
        UPDATE users
        SET groq_api_key = %s
        WHERE id = %s
        RETURNING id, (groq_api_key IS NOT NULL) AS has_api_key;
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (api_key, user_id))
                row = cur.fetchone()
            conn.commit()

        if row is None:
            raise HTTPException(status_code=404, detail="User not found")

        has_api_key = _row_value(row, "has_api_key", 1)
        return {"user_id": user_id, "has_api_key": has_api_key}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/api-key")
def get_api_key_status(user_id: int):
    """Whether this student has their own Groq key set - never the key itself."""
    query = "SELECT (groq_api_key IS NOT NULL) AS has_api_key FROM users WHERE id = %s;"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id,))
                row = cur.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="User not found")

        has_api_key = _row_value(row, "has_api_key", 0)
        return {"user_id": user_id, "has_api_key": has_api_key}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

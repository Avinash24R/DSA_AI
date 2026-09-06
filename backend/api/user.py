
from typing import Any, cast

from fastapi import APIRouter, HTTPException
from backend.schemas.user import UserCreate
from scripts.setup import get_connection
router = APIRouter(prefix="/api/users", tags=["user"])

@router.post("")
def create_user(user:UserCreate):
    query = """
    INSERT INTO users(name,email,level, codeforces_handle)
    VALUES(%s,%s,%s,%s)
    ON CONFLICT(email)
    DO UPDATE SET
        name=EXCLUDED.name,
        level=EXCLUDED.level,
        codeforces_handle=EXCLUDED.codeforces_handle
    RETURNING id,name,email,level,codeforces_handle;
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user.name, user.email, user.level, user.codeforces_handle))
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
            }

        return {
            "user_id": user_row["id"],
            "name": user_row["name"],
            "email": user_row["email"],
            "level": user_row["level"],
            "codeforces_handle": user_row["codeforces_handle"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

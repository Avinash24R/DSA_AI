from pydantic import BaseModel , Field

class UserCreate(BaseModel):
    name: str = Field( min_length=2 , max_length=100)
    email: str
    level: str = "Beginner"
    codeforces_handle: str | None = None
    leetcode_handle: str | None = None
    # The student's own Groq API key. Optional - when omitted/blank the
    # app falls back to the shared GROQ_API key from the backend's env.
    # Never echoed back in any API response (see backend/api/user.py).
    groq_api_key: str | None = None

class UserResponse(BaseModel):
    user_id : int
    name: str
    email: str
    level: str
    has_api_key: bool = False


class ApiKeyUpdate(BaseModel):
    groq_api_key: str | None = Field(
        default=None,
        description="Set to a new key, or null/empty string to clear it and fall back to the shared key.",
    )


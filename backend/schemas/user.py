from pydantic import BaseModel , Field

class UserCreate(BaseModel):
    name: str = Field( min_length=2 , max_length=100)
    email: str
    level: str = "Beginner"
    codeforces_handle: str | None = None
    leetcode_handle: str | None = None

class UserResponse(BaseModel):
    user_id : int
    name: str
    email: str
    level: str

